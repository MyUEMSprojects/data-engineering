# Spark 4.0 + conector Kafka PRÉ-BAIXADO (sem internet em tempo de execução) + clientes Python.
FROM apache/spark:4.0.0
USER root
RUN pip install --no-cache-dir pytest==8.3.4 confluent-kafka==2.8.0 "psycopg[binary]==3.2.3" \
 && mkdir -p /app /work /data /opt/ivy \
 && chown -R spark:spark /app /work /data /opt/ivy \
 && mkdir -p /opt/spark/conf && printf 'spark.jars.ivy /opt/ivy\nspark.jars.packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0\nspark.sql.session.timeZone UTC\n' \
      >> /opt/spark/conf/spark-defaults.conf
USER spark
WORKDIR /work
ENV PYTHONPATH=/app/src:/opt/spark/python:/opt/spark/python/lib/py4j-0.10.9.9-src.zip
# Resolve e guarda em /opt/ivy os JARs do conector (spark-sql-kafka, kafka-clients, commons-pool2, ...).
RUN echo "print('ok')" > /tmp/noop.py && /opt/spark/bin/spark-submit --master local[1] /tmp/noop.py 2>&1 | grep -E "^ok|downloading|FAILED" | head -5
