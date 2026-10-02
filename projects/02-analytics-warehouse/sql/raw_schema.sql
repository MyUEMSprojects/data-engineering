-- Camada RAW: espelho da origem (OLTP simulado), sem transformação. Carregada por scripts/load_raw.py.
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id text, name text, email text, uf text, segment text,
    updated_at timestamptz, _loaded_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS raw.products (
    product_id text, name text, category text, list_price numeric(12,2),
    updated_at timestamptz, _loaded_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS raw.orders (
    order_id text, customer_id text, order_ts timestamptz, status text,
    updated_at timestamptz, _loaded_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS raw.order_items (
    order_id text, line_no int, product_id text, quantity int,
    unit_price numeric(12,2), discount numeric(5,4),
    _loaded_at timestamptz DEFAULT now()
);
