# Pacote `basic_etl`

Módulos: `extract` (CSV/API), `transform` (funções **puras** de validação e deduplicação), `load` (upsert idempotente + quarentena), `pipeline` (orquestra e aplica o *gate* de taxa de rejeição) e `__main__` (CLI). Regra do projeto: a lógica de negócio fica em `transform`, sem I/O, para ser testável sem banco.
