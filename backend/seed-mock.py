#!/usr/bin/env python3
"""
Populate Neon retail schema with mock data.
Run:  pip install faker tqdm psycopg2-binary
"""

import random
from datetime import timedelta
from pathlib import Path
from decimal import Decimal

import psycopg2
from faker import Faker
from psycopg2.extras import execute_values          # ← make sure this line exists
from tqdm import tqdm

# ---------- DB connection ----------
DB_HOST = "ep-old-fire-a2imcysh-pooler.eu-central-1.aws.neon.tech"
DB_PORT = 5432
DB_NAME = "neondb"
DB_USER = "neondb_owner"
DB_PASS = "npg_yUzAue68mWCH"

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    sslmode="require",
)
fake = Faker()
cur = conn.cursor()

def rand_price():
    return round(random.uniform(10, 250), 2)

def flush(table):
    cur.execute(f"TRUNCATE {table} CASCADE")

# ---------- 1. categories ----------
categories = ["electronics", "books", "fashion", "kitchen", "outdoors"]
flush("categories")
execute_values(
    cur,
    "INSERT INTO categories (name) VALUES %s",
    [(cat,) for cat in categories],
)
cur.execute("SELECT id, name FROM categories")
cat_map = {name: cid for cid, name in cur.fetchall()}

# ---------- 2. products ----------
flush("products")
products = []
for cat in categories:
    for _ in range(20):
        products.append(
            (
                fake.word().capitalize() + " " + fake.word().capitalize(),
                fake.unique.bothify(text="SKU-#####"),
                cat_map[cat],
                rand_price(),
                random.randint(0, 100),
                fake.sentence(),
                fake.image_url(),
                True,
            )
        )

execute_values(
    cur,
    """
    INSERT INTO products
      (name, sku, category_id, price, stock_qty, description, image_url, is_active)
    VALUES %s
    """,
    products,
)
cur.execute("SELECT id, price FROM products")
product_rows = cur.fetchall()

# ---------- 3. customers & addresses ----------
flush("addresses")
flush("customers")

customers = []
for _ in range(50):
    first, last = fake.first_name(), fake.last_name()
    customers.append((first, last, fake.unique.email(), fake.phone_number()))

execute_values(                               # ← fixed bulk insert
    cur,
    """
    INSERT INTO customers (first_name, last_name, email, phone)
    VALUES %s
    RETURNING id
    """,
    customers,
)
customer_ids = [row[0] for row in cur.fetchall()]

addresses = []
for cid in customer_ids:
    for _ in range(random.randint(1, 2)):
        addresses.append(
            (
                cid,
                fake.street_address(),
                "",
                fake.city(),
                fake.postcode(),
                fake.country_code(),
            )
        )

execute_values(
    cur,
    """
    INSERT INTO addresses
      (customer_id, line1, line2, city, postcode, country)
    VALUES %s
    """,
    addresses,
)

# ---------- 4. orders + order_items ----------
flush("order_items")
flush("orders")

orders = []
for _ in tqdm(range(75), desc="orders"):
    cid = random.choice(customer_ids)
    status = random.choice(["processing", "paid", "shipped", "delivered"])
    placed_at = fake.date_time_between(start_date="-90d", end_date="now")
    orders.append((cid, status, 0, placed_at))

execute_values(
    cur,
    """
    INSERT INTO orders (customer_id, status, total_amount, placed_at)
    VALUES %s
    RETURNING id
    """,
    orders,
)
order_ids = [row[0] for row in cur.fetchall()]

order_items = []
for oid in order_ids:
    chosen_products = random.sample(product_rows, random.randint(1, 4))
    total = 0
    for pid, price in chosen_products:
        price = Decimal(str(price)) 
        qty = random.randint(1, 3)
        order_items.append((oid, pid, qty, price))
        total += price * qty
    cur.execute("UPDATE orders SET total_amount=%s WHERE id=%s", (total, oid))

execute_values(
    cur,
    """
    INSERT INTO order_items (order_id, product_id, qty, unit_price)
    VALUES %s
    """,
    order_items,
)

# ---------- 5. complaints ----------
flush("complaints")
complaints = []
for _ in range(15):
    complaints.append(
        (
            random.choice(customer_ids),
            random.choice(order_ids),
            fake.sentence(nb_words=12),
            random.choice(["open", "resolved", "pending"]),
        )
    )

execute_values(
    cur,
    """
    INSERT INTO complaints (customer_id, order_id, text, status)
    VALUES %s
    """,
    complaints,
)

conn.commit()
cur.close()
conn.close()
print("🎉 Mock data inserted successfully!")