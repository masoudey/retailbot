/*--------------------------------------------------------------------
  Top-level helpers
--------------------------------------------------------------------*/
DO $$ BEGIN
    -- order status enum
    CREATE TYPE order_status AS ENUM
      ('processing','paid','shipped','delivered','cancelled','returned');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    -- shipment status enum
    CREATE TYPE shipment_status AS ENUM
      ('pending','in_transit','delivered','returned');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

/*--------------------------------------------------------------------
  Customers & addresses
--------------------------------------------------------------------*/
CREATE TABLE IF NOT EXISTS customers (
    id           SERIAL PRIMARY KEY,
    first_name   TEXT,
    last_name    TEXT,
    email        TEXT UNIQUE NOT NULL,
    phone        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS addresses (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    line1       TEXT NOT NULL,
    line2       TEXT,
    city        TEXT NOT NULL,
    postcode    TEXT,
    country     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

/*--------------------------------------------------------------------
  Catalogue
--------------------------------------------------------------------*/
CREATE TABLE IF NOT EXISTS categories (
    id         SERIAL PRIMARY KEY,
    name       TEXT UNIQUE NOT NULL,
    parent_id  INTEGER REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS products (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    sku          TEXT UNIQUE,
    category_id  INTEGER REFERENCES categories(id),
    price        NUMERIC(10,2) NOT NULL,
    stock_qty    INTEGER DEFAULT 0,
    description  TEXT,
    image_url    TEXT,
    link         TEXT,
    is_active    BOOLEAN DEFAULT TRUE
);

/*--------------------------------------------------------------------
  Orders, items, payments, shipments
--------------------------------------------------------------------*/
CREATE TABLE IF NOT EXISTS orders (
    id            SERIAL PRIMARY KEY,
    customer_id   INTEGER REFERENCES customers(id),
    session_id   TEXT REFERENCES sessions(id),
    status        order_status DEFAULT 'processing',
    total_amount  NUMERIC(10,2),
    placed_at     TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS payments (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER REFERENCES orders(id),
    provider        TEXT,
    provider_txn_id TEXT,
    amount          NUMERIC(10,2),
    currency        TEXT DEFAULT 'USD',
    status          TEXT,
    paid_at         TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS shipments (
    id            SERIAL PRIMARY KEY,
    order_id      INTEGER REFERENCES orders(id),
    address_id    INTEGER REFERENCES addresses(id),
    carrier       TEXT,
    tracking_no   TEXT,
    status        shipment_status DEFAULT 'pending',
    shipped_at    TIMESTAMPTZ,
    delivered_at  TIMESTAMPTZ
);

/*--------------------------------------------------------------------
  Complaints (matches Rasa action)
--------------------------------------------------------------------*/
CREATE TABLE IF NOT EXISTS complaints (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_id    INTEGER REFERENCES orders(id),
    text        TEXT,
    status      TEXT DEFAULT 'open',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

/*--------------------------------------------------------------------
  Chat sessions
--------------------------------------------------------------------*/
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,                -- tracker.sender_id
    customer_id INTEGER REFERENCES customers(id),
    messages    JSONB       DEFAULT '[]',        -- array of {sender,text,ts}
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_items (
    session_id  TEXT   NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    product_id  INTEGER REFERENCES products(id) ON DELETE CASCADE,
    order_id   INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    qty         INTEGER NOT NULL CHECK (qty > 0),
    unit_price  NUMERIC(10,2) NOT NULL,
    added_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (session_id, product_id, order_id)
);