-- Destino idempotente: reprocessar a MESMA mensagem N vezes tem o mesmo efeito de processar 1 vez.

-- Histórico imutável: 1 linha por evento. A chave natural (order_id-seq) deduplica reentregas.
CREATE TABLE IF NOT EXISTS order_events (
    event_id        text PRIMARY KEY,
    order_id        text        NOT NULL,
    seq             int         NOT NULL CHECK (seq >= 1),
    customer_id     text        NOT NULL,
    status          text        NOT NULL,
    amount          numeric(12,2) NOT NULL CHECK (amount >= 0),
    event_ts        timestamptz NOT NULL,
    kafka_partition int,
    kafka_offset    bigint,
    ingested_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS order_events_order_idx ON order_events (order_id, seq);

-- Estado atual: só avança (seq maior vence) — protege contra reentrega e evento fora de ordem.
CREATE TABLE IF NOT EXISTS orders_current (
    order_id        text PRIMARY KEY,
    customer_id     text        NOT NULL,
    status          text        NOT NULL,
    amount          numeric(12,2) NOT NULL,
    seq             int         NOT NULL,
    updated_at      timestamptz NOT NULL
);
