-- Executado UMA vez na criação do container (docker-entrypoint-initdb.d).
CREATE DATABASE warehouse;
\connect warehouse

CREATE TABLE IF NOT EXISTS orders_daily (
    order_id     text PRIMARY KEY,
    customer_id  text           NOT NULL,
    amount       numeric(12, 2) NOT NULL CHECK (amount >= 0),
    status       text           NOT NULL,
    order_date   date           NOT NULL,
    created_at   timestamptz    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_daily_date ON orders_daily (order_date);

CREATE TABLE IF NOT EXISTS daily_summary (
    order_date  date PRIMARY KEY,
    orders      int            NOT NULL,
    revenue     numeric(14, 2) NOT NULL,
    updated_at  timestamptz    NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id          bigserial PRIMARY KEY,
    dag_run_id  text        NOT NULL,
    order_date  date        NOT NULL,
    rows_read   int         NOT NULL,
    rows_valid  int         NOT NULL,
    rows_rejected int       NOT NULL,
    finished_at timestamptz NOT NULL DEFAULT now()
);
