-- Schema do Projeto 01. Idempotente: pode ser executado várias vezes.
CREATE TABLE IF NOT EXISTS orders (
    order_id     text PRIMARY KEY,
    customer_id  text           NOT NULL,
    amount       numeric(12, 2) NOT NULL CHECK (amount >= 0),
    status       text           NOT NULL CHECK (status IN ('created', 'paid', 'shipped', 'canceled')),
    uf           char(2),
    created_at   timestamptz    NOT NULL,
    updated_at   timestamptz    NOT NULL,
    _loaded_at   timestamptz    NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at);

-- Quarentena: linhas rejeitadas na validação (não se perde dado, nem se propaga lixo).
CREATE TABLE IF NOT EXISTS orders_rejected (
    row_hash    text PRIMARY KEY,           -- md5(raw_row || reason): reexecutar não duplica
    run_id      text        NOT NULL,       -- run em que foi vista pela 1ª vez
    raw_row     jsonb       NOT NULL,
    reason      text        NOT NULL,
    rejected_at timestamptz NOT NULL DEFAULT now()
);
