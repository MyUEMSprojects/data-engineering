-- Resultado analítico (consultável por BI). Chave = a janela + a dimensão ⇒ UPSERT idempotente.
CREATE TABLE IF NOT EXISTS page_views_1m (
    window_start  timestamptz NOT NULL,
    page          text        NOT NULL,
    views         int         NOT NULL,
    users         int         NOT NULL,
    updated_batch bigint      NOT NULL,
    PRIMARY KEY (window_start, page)
);

-- Mensagens que não parseiam: guardadas com o motivo (nada some em silêncio). Chave = coordenadas Kafka.
CREATE TABLE IF NOT EXISTS stream_rejects (
    kafka_partition int    NOT NULL,
    kafka_offset    bigint NOT NULL,
    reason          text   NOT NULL,
    raw             text,
    PRIMARY KEY (kafka_partition, kafka_offset)
);

-- Livro-razão de micro-lotes aplicados: reexecutar o MESMO batch_id (após falha) vira no-op.
CREATE TABLE IF NOT EXISTS batch_log (
    query      text   NOT NULL,
    batch_id   bigint NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (query, batch_id)
);
