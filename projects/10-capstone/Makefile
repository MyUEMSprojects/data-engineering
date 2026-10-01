# `make ci` reproduz LOCALMENTE o que o GitHub Actions roda (.github/workflows/capstone.yml).
.PHONY: install lint test alerts image demo dag ci clean
PY ?= python
export PYTHONPATH := src

install:
	$(PY) -m pip install -r requirements.txt ruff black

lint:
	ruff check . && black --check .

test:
	pytest -q

alerts:
	docker run --rm --entrypoint promtool -v "$$PWD/monitoring:/m:ro" prom/prometheus:v2.55.1 check rules /m/alerts.yml

image:
	docker build -t capstone:local .

demo: image
	docker run --rm capstone:local demo

dag:
	docker run --rm -v "$$PWD/dags:/dags:ro" --entrypoint python apache/airflow:3.0.0 -c "\
from airflow.models.dagbag import DagBag; b = DagBag('/dags', include_examples=False); \
assert not b.import_errors, b.import_errors; print('OK', sorted(b.dags['capstone_daily'].task_ids))"

ci: lint test alerts demo dag

clean:
	rm -rf lake
