import os

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
PG_DSN = os.environ.get("PG_DSN", "postgresql://de:de@localhost:5432/sink")
TOPIC = os.environ.get("KPIPE_TOPIC", "orders.events")
DLQ_TOPIC = f"{TOPIC}.dlq"
PARTITIONS = int(os.environ.get("KPIPE_PARTITIONS", "6"))
