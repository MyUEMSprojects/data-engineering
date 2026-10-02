# Scripts

`verify_and_e2e.py`: verifica a infraestrutura criada (criptografia, versionamento, IAM por simulação) e executa o e2e S3→SQS→handler→curated/DLQ. Requer `AWS_ENDPOINT_URL` apontando para o emulador.
