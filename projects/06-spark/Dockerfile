# Spark 4.0 (Scala 2.13, Java 17, Python 3.10) + pytest para os testes dentro do contêiner.
FROM apache/spark:4.0.0
USER root
RUN pip install --no-cache-dir pytest==8.3.4 \
 && mkdir -p /app /data /work && chown -R spark:spark /app /data /work
USER spark
WORKDIR /work
ENV PYTHONPATH=/app/src:/opt/spark/python:/opt/spark/python/lib/py4j-0.10.9.9-src.zip
