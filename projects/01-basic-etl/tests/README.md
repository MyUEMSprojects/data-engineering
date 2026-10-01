# Testes

`test_transform.py`, `test_extract.py` e `test_pipeline.py` rodam **sem infraestrutura**; `test_load_integration.py` precisa do PostgreSQL do Compose (marcado `integration`). Execução: `pytest -q -m 'not integration'`.
