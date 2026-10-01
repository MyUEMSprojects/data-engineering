# Erros e logging

> 🔵 Core · Parte de [04 — Python para DE](../README.md)

Pipelines falham, e precisam falhar **de forma clara e recuperável**. Este tópico
cobre tratamento de exceções e logging — a diferença entre um job que "morreu sem
explicação" e um que te diz exatamente o que aconteceu.

## Parte 1 — Exceptions

### O modelo

Erros em Python sobem como **exceptions**; se ninguém as trata, o programa termina
com um *traceback*. Você decide onde capturar e como reagir.

```python
try:
    df = read_csv(path)
except FileNotFoundError:
    log.error("Arquivo não encontrado: %s", path)
    raise                     # re-levanta: não engula o erro
except ValueError as e:
    log.warning("CSV malformado (%s), pulando", e)
else:
    process(df)               # roda só se o try teve sucesso
finally:
    cleanup()                 # sempre roda (fechar conexões/arquivos)
```

### Regras de ouro

- **Capture exceções específicas**, não `except Exception` genérico (e **nunca**
  `except:` pelado — captura até `KeyboardInterrupt`).
- **Não engula erros** silenciosamente (`except: pass` é um crime em pipelines —
  esconde corrupção de dados).
- **Falhe cedo e alto** quando o dado está inválido e não há como prosseguir com
  segurança (melhor quebrar que gravar lixo).
- Preserve o contexto: `raise NovoErro(...) from e` encadeia a causa.

### Exceptions customizadas

```python
class DataQualityError(Exception):
    """Dados violaram uma expectativa de qualidade."""

def validar(df):
    if df["id"].isnull().any():
        raise DataQualityError("coluna id contém nulos")
```

Exceções próprias deixam o tratamento semântico ("isso é um problema de
qualidade", não "um ValueError qualquer").

### Erros transitórios vs permanentes

Distinga o que **vale retentar** (timeout de rede, 503) do que **não** (404,
credencial inválida, dado malformado). Retry só faz sentido para erros
transitórios — ver [HTTP clients/retries](../08-http-clients/README.md) e
[idempotência](../../09-etl-elt/07-idempotency-retries/README.md).

## Parte 2 — Logging

### Por que `logging`, não `print`

`print` vai só para stdout, sem nível, sem timestamp, sem contexto, difícil de
desligar/rotear. O módulo `logging` dá níveis, destinos configuráveis e formato —
essencial para [observabilidade](../../24-observability/01-logging/README.md).

### Configuração básica

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)     # um logger por módulo

log.debug("detalhe para depuração")
log.info("ingeridas %d linhas de %s", n, tabela)   # use %s, não f-string
log.warning("coluna %s tem %d nulos", col, nulos)
log.error("falha ao conectar: %s", e)
log.exception("erro inesperado")      # inclui o traceback (dentro de except)
```

> Prefira `log.info("x=%s", x)` a `log.info(f"x={x}")`: a interpolação só acontece
> se o nível estiver ativo (micro-otimização) e integra melhor com ferramentas.

### Níveis (e quando usar)

| Nível | Uso |
| --- | --- |
| DEBUG | detalhes finos (dev/diagnóstico) |
| INFO | progresso normal ("ingeridas N linhas") |
| WARNING | algo estranho, mas o job segue (dado pulado) |
| ERROR | falhou uma operação |
| CRITICAL | o sistema não pode continuar |

### Logging estruturado (produção)

Em produção, logs em **JSON** (com campos: pipeline, tabela, partição,
`run_id`, contagens) são filtráveis e agregáveis por ferramentas de log. Bibliotecas:
`structlog`, ou um `Formatter` JSON customizado.

```python
log.info("ingest_done", extra={"table": "orders", "rows": n, "run_id": rid})
```

### O que logar em pipelines

- Início/fim de cada etapa, com **contagens** e **duração**.
- Decisões de qualidade (linhas rejeitadas, dedupe).
- Erros com contexto suficiente para reproduzir.
- **Nunca** segredos ou PII (ver [security](../../26-security/07-data-masking-pii/README.md)).

## Erros comuns

- `except Exception: pass` → falhas e corrupção invisíveis.
- `print` em vez de `logging`.
- Logs sem contexto ("erro") que não ajudam a diagnosticar.
- Logar segredos/PII.
- Retentar erros permanentes (ex.: 404) em loop infinito.

## Boas práticas

- Um logger por módulo (`getLogger(__name__)`).
- Configure logging no *entrypoint* da aplicação, não em cada módulo.
- Logs estruturados + contagens + `run_id` para rastrear execuções.
- `log.exception` dentro de `except` para capturar o traceback.

## Relação com outros conceitos

- Base de [observabilidade/logging](../../24-observability/01-logging/README.md) e
  [troubleshooting](../../02-linux-shell-environment/08-logs-and-troubleshooting/README.md).
- Retries conectam a [HTTP clients](../08-http-clients/README.md) e
  [fault tolerance](../../10-data-pipelines/05-fault-tolerance/README.md).

## Exercícios

1. Reescreva um script cheio de `print` usando `logging` com níveis e contexto.
2. Crie uma exception `SchemaError` e levante-a quando uma coluna esperada faltar.
3. Classifique 5 erros de um pipeline em transitórios vs permanentes e diga quais
   retentaria.
4. Configure logs em JSON com campos `table`, `rows`, `run_id` e filtre por tabela.

## Referências

- Documentação de `logging` (docs.python.org) — HOWTO e Cookbook.
- `structlog` (structlog.org).
- Slatkin, B. *Effective Python* — itens sobre exceções.
