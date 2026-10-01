FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
ENV PYTHONPATH=/app/src CAPSTONE_LAKE=/lake
RUN useradd -m app && mkdir /lake && chown app /lake
USER app
ENTRYPOINT ["python", "-m", "capstone"]
