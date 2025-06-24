"""
actions.py
Custom actions for the retail bot, wired to Neon PostgreSQL.


"""

from __future__ import annotations

import logging
import random
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Text

import psycopg2
from psycopg2.extras import RealDictCursor
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SessionStarted, ActionExecuted

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# DB connection & schema bootstrapping
# ──────────────────────────────────────────────────────────
DB_HOST = "ep-old-fire-a2imcysh-pooler.eu-central-1.aws.neon.tech"
DB_PORT = 5432
DB_NAME = "neondb"
DB_USER = "neondb_owner"
DB_PASS = "npg_yUzAue68mWCH"
DB_SSLMODE = "require"

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def get_db_connection():
    """Return a psycopg2 connection with dict rows."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        sslmode=DB_SSLMODE,
        cursor_factory=RealDictCursor,
    )


def init_schema() -> None:
    """Run schema.sql (if present) once at import time."""
    if not SCHEMA_FILE.exists():
        logger.warning("schema.sql not found – skipping bootstrap")
        return
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(SCHEMA_FILE.read_text())
            conn.commit()
            logger.info("Schema checked/created")
    except Exception as e:
        logger.error("Schema init failed: %s", e)


def fetchone(query: str, params: tuple | list = ()) -> Optional[Dict[str, Any]]:
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("fetchone: %s", e)
        return None


def fetchall(query: str, params: tuple | list = ()) -> List[Dict[str, Any]]:
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error("fetchall: %s", e)
        return []


def execute(query: str, params: tuple | list = ()) -> Any:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # debug prints
        print(f"[execute] ▶️ SQL: {query}")
        print(f"[execute] ▶️ Params: {params!r}")

        cur.execute(query, params)

        result = None
        # only try fetching if the statement returned rows (e.g. RETURNING)
        if cur.description:
            row = cur.fetchone()
            print(f"[execute] 👀 raw fetched row: {row!r}")

            if row is not None:
                # handle both tuple and dict cursors
                if isinstance(row, dict):
                    result = next(iter(row.values()))
                else:
                    result = row[0]
            print(f"[execute] ✅ returning result: {result!r}")

        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        print(f"[execute] ❌ exception: {e}")
        return None

    finally:
        cur.close()
        conn.close()


# Run schema check immediately
init_schema()

# ──────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────
def update_order_status(order_id: int | str, new_status: str) -> bool:
    rows = execute(
        "UPDATE orders SET status=%s WHERE id=%s AND status != %s RETURNING id",
        (new_status, order_id, new_status),
    )
    return bool(rows)

def append_session_message(session_id: str, sender: str, text: str) -> None:
    """
    Appends one message object to the JSONB 'messages' array for this session.
    """
    # Build the JSON array literal of one element:
    msg_obj = {
        "sender": sender,
        "text": text,
        "ts": datetime.utcnow().isoformat()
    }
    # We wrap it in [] so JSONB concatenation works:
    payload = json.dumps([msg_obj])
    execute(
        """
        UPDATE sessions
           SET messages = messages || %s::jsonb
             , updated_at = NOW()
         WHERE id = %s
        """,
        (payload, session_id),
    )

# ──────────────────────────────────────────────────────────
# Core actions
# ──────────────────────────────────────────────────────────

class ActionSaveMessage(Action):
    def name(self) -> Text:
        return "action_save_message"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict,
    ) -> list:
        # Grab the latest user message
        user_text = tracker.latest_message.get("text") or ""
        session_id = tracker.sender_id

        # Ensure session row exists
        execute(
            "INSERT INTO sessions (id) VALUES (%s) ON CONFLICT (id) DO NOTHING",
            (session_id,),
        )
        # Append this user message
        append_session_message(session_id, "user", user_text)

        return []

class ActionSessionStart(Action):
    def name(self) -> str:
        return "action_session_start"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict,
    ) -> list:
        # 1) Run the default session start events
        events = [SessionStarted(), ActionExecuted("action_listen")]

        # 2) Create a session row in the DB (if it doesn't already exist)
        session_id = tracker.sender_id
        execute(
            """
            INSERT INTO sessions (id, created_at, updated_at)
            VALUES (%s, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
            """,
            (session_id,),
        )

        # 3) Return the events so Rasa continues as normal
        return events
    
class ActionCheckOrderStatus(Action):
    def name(self) -> Text: return "action_check_order_status"

    async def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message("I didn’t get an order ID. Could you repeat it?")
            return []
        row = fetchone("SELECT status FROM orders WHERE id=%s", (order_id,))
        if row:
            return [SlotSet("order_status", row["status"])]
        dispatcher.utter_message("Sorry, I can’t find that order.")
        return [SlotSet("order_status", None)]


class ActionRecommendProducts(Action):
    """Return up to five active products from the requested category."""

    def name(self) -> Text:
        return "action_recommend_products"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # ── Fallback logic ──────────────────────────────────────────
        # 1. Try the slot set by NLU/entity extraction.
        # 2. If the slot is empty, fall back to the raw user message
        #    (handles one-word replies like “books”).
        raw_msg: str = (tracker.latest_message.get("text") or "").strip().lower()
        category: str = (tracker.get_slot("product_category") or raw_msg).lower()

        if not category:
            dispatcher.utter_message(
                "Please tell me which category you’re interested in."
            )
            return []

        # ── Fetch products from DB ──────────────────────────────────
        products = fetchall(
            """
            SELECT p.name,
                   p.price,
                   COALESCE(p.link, '#') AS link
            FROM   products p
            JOIN   categories c ON c.id = p.category_id
            WHERE  p.is_active
              AND  LOWER(c.name) = %s
            ORDER  BY p.name
            LIMIT  5
            """,
            (category,),
        )

        if not products:
            dispatcher.utter_message(f"Sorry, no items found in {category}.")
            return [SlotSet("recommendations", None)]

        # build nice bullet list
        recs_text = "\n".join(
            f"- {row['name']} (${row['price']}): {row['link']}" for row in products
        )

        dispatcher.utter_message(
            f"Based on your interest in {category}, here are some recommendations:\n{recs_text}"
        )
        return []
    
class ActionProductDetails(Action):
    def name(self) -> Text:          # noqa: D401
        return "action_product_details"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        product_name = tracker.get_slot("product_details")
        print(f"[ProductDetails] Looking up product: {product_name!r}")
        if not product_name:
            dispatcher.utter_message("Which product would you like details about?")
            return []

        row = fetchone(
            """
            SELECT name, price, stock_qty, description, link
            FROM   products
            WHERE  LOWER(name) = %s OR sku = %s
            LIMIT  1
            """,
            (product_name.lower(), product_name.upper()),
        )

        if not row:
            dispatcher.utter_message("Sorry, I couldn’t find that product.")
            return []

        msg = (
            f"*{row['name']}* – **${row['price']}**\n"
            f"{row['description']}\n"
            f"Stock: {row['stock_qty']}\n"
            f"[View product]({row['link']})"
        )
        dispatcher.utter_message(msg)
        # Keep slot set so the user can immediately say “Buy it”
        return []
# ──────────────────────────────────────────────────────────
# Add-to-cart helper
# ──────────────────────────────────────────────────────────

class ActionAddToCart(Action):
    """Adds (or increments) a product in the user’s cart_items."""

    def name(self) -> Text:
        return "action_add_to_cart"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        session_id   = tracker.sender_id
        product_name = (tracker.get_slot("product_to_order") or "").strip()
        quantity_raw = (tracker.get_slot("quantity") or "1").strip()

        # 1) Ensure session exists
        print(f"[AddToCart] Ensuring session {session_id} exists")
        execute(
            "INSERT INTO sessions (id) VALUES (%s) ON CONFLICT DO NOTHING",
            (session_id,),
        )

        # 2) Find or create "open" order for this session
        order = fetchone(
            "SELECT id, total_amount FROM orders "
            "WHERE session_id = %s AND status = 'processing'",
            (session_id,),
        )
        print(f"[AddToCart] Fetched existing order row: {order}")
        if order:
            order_id      = order["id"]
            current_total = Decimal(order["total_amount"])
            print(f"[AddToCart] Using existing order_id={order_id}, current_total={current_total}")
        else:
            print(f"[AddToCart] No existing order for session {session_id}, creating one")
            order_id = execute(
                "INSERT INTO orders (session_id, total_amount) "
                "VALUES (%s, %s) RETURNING id",
                (session_id, Decimal("0.00")),
            )
            print(f"[AddToCart] Created new order, returned order_id={order_id}")
            if order_id is None:
                dispatcher.utter_message("❌ Sorry, I couldn’t start your cart. Please try again.")
                return []
            current_total = Decimal("0.00")

        # 3) Basic validation: product exists & quantity parse
        if not product_name:
            dispatcher.utter_message("Which product would you like to add?")
            return []
        try:
            quantity = max(1, int(quantity_raw))
        except ValueError:
            dispatcher.utter_message("How many would you like to add?")
            return []

        prod = fetchone(
            "SELECT id, name, price FROM products WHERE LOWER(name) = %s LIMIT 1",
            (product_name.lower(),),
        )
        print(f"[AddToCart] Looked up product: {prod}")
        if not prod:
            dispatcher.utter_message("I couldn't find that product in our catalog.")
            return []

        # 4) Upsert into cart_items (only if we have a valid order_id)
        if order_id:
            print(f"[AddToCart] Inserting/updating cart_items for order_id={order_id}, product_id={prod['id']}, qty={quantity}")
            execute(
                """
                INSERT INTO cart_items (order_id, product_id, qty, unit_price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id, product_id)
                DO UPDATE SET qty = cart_items.qty + EXCLUDED.qty
                """,
                (order_id, prod["id"], quantity, Decimal(prod["price"])),
            )
        else:
            dispatcher.utter_message("❌ Something went wrong: no order to attach the item to.")
            return []

        # 5) Update order total_amount
        new_total = current_total + Decimal(prod["price"]) * quantity
        print(f"[AddToCart] Updating order {order_id} total from {current_total} to {new_total}")
        execute(
            "UPDATE orders SET total_amount = %s WHERE id = %s",
            (new_total, order_id),
        )

        dispatcher.utter_message(
            f"✅ Added {quantity} × *{prod['name']}* to your cart."
        )
        # reset for next time
        return [SlotSet("quantity", None)]



class ActionTrackShipment(Action):
    def name(self) -> Text: return "action_track_shipment"

    async def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message("Order ID please?")
            return []
        row = fetchone(
            """
            SELECT carrier, tracking_no, status
            FROM shipments
            WHERE order_id = %s
            """,
            (order_id,),
        )
        if row:
            msg = (
                f"Carrier: {row['carrier']}\n"
                f"Tracking #: {row['tracking_no']}\n"
                f"Status: {row['status']}"
            )
        else:
            msg = "No shipment info yet. It may still be processing."
        dispatcher.utter_message(msg)
        return []


class ActionCancelOrder(Action):
    def name(self) -> Text: return "action_cancel_order"

    async def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message("Provide the order ID you wish to cancel.")
            return []
        cancelled = update_order_status(order_id, "cancelled")
        dispatcher.utter_message(
            "✅ Order cancelled." if cancelled else "Unable to cancel (maybe already shipped?)."
        )
        return []


class ActionReturnOrder(Action):
    def name(self) -> Text: return "action_return_order"

    async def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message("Which order would you like to return?")
            return []
        ok = execute(
            """
            UPDATE orders SET status='returned'
            WHERE id=%s AND status='delivered'
            RETURNING id
            """,
            (order_id,),
        )
        dispatcher.utter_message(
            "Return initiated! We’ll email the label." if ok else "Order not eligible for return."
        )
        return []


class ActionListCategories(Action):
    def name(self) -> Text: return "action_list_categories"

    async def run(self, dispatcher, tracker, domain):
        cats = fetchall("SELECT name FROM categories ORDER BY name")
        cat_list = ", ".join(c["name"].title() for c in cats) if cats else "No categories found."
        dispatcher.utter_message(cat_list)
        return []


class ActionProductSearch(Action):
    def name(self) -> Text: return "action_product_search"

    async def run(self, dispatcher, tracker, domain):
        term = tracker.get_slot("search_term") or ""
        if not term.strip():
            dispatcher.utter_message("What product are you looking for?")
            return []
        like = f"%{term.lower()}%"
        rows = fetchall(
            "SELECT name, price FROM products WHERE LOWER(name) LIKE %s LIMIT 6", (like,)
        )
        msg = (
            "\n".join(f"- {r['name']} – ${r['price']}" for r in rows)
            if rows
            else "No matching products."
        )
        dispatcher.utter_message(msg)
        return []


class ActionProductAvailability(Action):
    def name(self) -> Text: return "action_product_availability"

    async def run(self, dispatcher, tracker, domain):
        product = tracker.get_slot("product_to_order")
        if not product:
            dispatcher.utter_message("Which product?")
            return []
        row = fetchone(
            "SELECT stock_qty FROM products WHERE LOWER(name) = %s", (product.lower(),)
        )
        if row:
            qty = row["stock_qty"]
            dispatcher.utter_message(
                f"We have {qty} left in stock." if qty else "Out of stock at the moment."
            )
        else:
            dispatcher.utter_message("Product not found.")
        return []


class ActionUpdateAddress(Action):
    def name(self) -> Text: return "action_update_address"

    async def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        new_addr = tracker.get_slot("new_shipping_address")
        if not order_id or not new_addr:
            dispatcher.utter_message("I need the order ID and the new address.")
            return []
        execute(
            "UPDATE orders SET address=%s WHERE id=%s AND status='processing'",
            (new_addr, order_id),
        )
        dispatcher.utter_message("Address updated if the order was still processing.")
        return []


class ActionStoreHours(Action):
    def name(self) -> Text: return "action_store_hours"

    async def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message("We’re open 9 AM – 6 PM, Monday to Saturday (CET).")
        return []


# ──────────────────────────────────────────────────────────
# Additional multi-step actions
# ──────────────────────────────────────────────────────────
class ActionPlaceOrder(Action):
    def name(self) -> Text: return "action_place_order"

    async def run(self, dispatcher, tracker, domain):
        product_name = tracker.get_slot("product_to_order")
        quantity = tracker.get_slot("quantity")
        address = tracker.get_slot("shipping_address")

        if not product_name:
            dispatcher.utter_message("Which product would you like to order?")
            return []
        if not quantity:
            dispatcher.utter_message("How many would you like to buy?")
            return []
        if not address:
            dispatcher.utter_message("Where should we ship your order?")
            return []

        prod_row = fetchone(
            "SELECT id, price FROM products WHERE LOWER(name) = %s LIMIT 1",
            (product_name.lower(),),
        )
        if not prod_row:
            dispatcher.utter_message("Sorry, that product isn’t in our catalog yet.")
            return []

        product_id = prod_row["id"]
        unit_price = Decimal(prod_row["price"])
        qty_int = int(quantity)
        total_cost = unit_price * qty_int

        new_order_id = execute(
            """
            INSERT INTO orders (customer_id, status, total_amount, address)
            VALUES (NULL, 'processing', %s, %s)
            RETURNING id
            """,
            (total_cost, address),
        )

        if new_order_id:
            execute(
                """
                INSERT INTO order_items (order_id, product_id, qty, unit_price)
                VALUES (%s, %s, %s, %s)
                """,
                (new_order_id, product_id, qty_int, unit_price),
            )

        order_id_display = str(new_order_id) if new_order_id else str(random.randint(10000, 99999))

        dispatcher.utter_message(
            f"Great! Your order for {quantity} × {product_name} will be shipped to {address}. "
            f"Your order number is {order_id_display}."
        )
        return [
            SlotSet("order_id", order_id_display),
            SlotSet("product_to_order", None),
            SlotSet("quantity", None),
            SlotSet("shipping_address", None),
        ]


class ActionLogComplaint(Action):
    def name(self) -> Text: return "action_log_complaint"

    async def run(self, dispatcher, tracker, domain):
        complaint_text = tracker.latest_message.get("text")
        if complaint_text:
            execute(
                "INSERT INTO complaints (customer_id, order_id, text) VALUES (NULL, NULL, %s)",
                (complaint_text,),
            )
        dispatcher.utter_message(
            f'Logging your complaint: "{complaint_text}". Our support team will follow up.'
        )
        return []