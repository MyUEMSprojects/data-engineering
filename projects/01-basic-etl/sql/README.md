# SQL

`schema.sql`: DDL do destino PostgreSQL (tabela de pedidos com chave primária para *upsert* e tabela de quarentena com `row_hash`). Carregado automaticamente pelo `docker-compose.yml` na primeira subida.
