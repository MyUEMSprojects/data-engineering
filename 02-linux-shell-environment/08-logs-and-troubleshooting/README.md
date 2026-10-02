# Logs e troubleshooting

> 🟢 Foundations · Parte de [02 — Linux & Shell](../README.md)

## Por que isso é uma habilidade central

Pipelines falham — é uma questão de quando, não se. A diferença entre um DE júnior
e um sênior muitas vezes é a **velocidade e o método** para diagnosticar "por que
o job quebrou / está lento / sumiu". Este tópico reúne onde olhar e como pensar.
A observabilidade "de produto" (métricas, tracing, SLOs) está no
[módulo 24](../../24-observability/README.md); aqui é o troubleshooting no nível
de SO.

## Onde ficam os logs

```text
/var/log/syslog | /var/log/messages   # log geral do sistema
/var/log/<serviço>/                    # logs por serviço
journalctl                             # logs do systemd (distros modernas)
<app>/logs/ ou stdout do container     # logs da sua aplicação/pipeline
```

### journalctl (systemd)

```bash
journalctl -u meu-servico              # logs de um serviço
journalctl -u meu-servico -f           # segue em tempo real
journalctl -u meu-servico --since "1 hour ago"
journalctl -k                          # mensagens do kernel (ex.: OOM killer)
journalctl -p err                      # só nível error ou pior
```

### Logs de aplicação e container

```bash
tail -f app.log                        # acompanha
docker logs -f <container>             # logs de um container
docker logs --since 10m <container>
kubectl logs -f <pod>                  # em Kubernetes
```

## Método de diagnóstico (um roteiro)

1. **Reproduza/localize o erro.** Qual job, qual execução, qual horário?
2. **Leia a mensagem de erro inteira** — inclusive o *traceback* completo, não só
   a última linha. A causa raiz costuma estar no topo do *stack*.
3. **Isole a camada:** é dado? código? infra (CPU/mem/disco/rede)? permissão?
   dependência externa (API/DB fora)?
4. **Verifique recursos** (abaixo).
5. **Compare com a última execução boa:** o que mudou? (deploy, dados, schema,
   cota, credencial expirada?)
6. **Forme uma hipótese, teste-a, registre o que aprendeu.**

## Checklist de recursos do sistema

```bash
df -h            # disco cheio? (causa clássica de falha de escrita)
df -i            # inodes esgotados? (muitos arquivos pequenos)
free -h          # memória; swap em uso?
top / htop       # CPU e memória por processo
uptime           # load average alto?
journalctl -k | grep -i oom    # o OOM killer matou seu processo?
iostat -x 1      # I/O de disco (pacote sysstat)
```

## Rede (APIs, bancos, brokers fora do ar)

```bash
ping host                      # host responde?
curl -v https://api.exemplo.com/health   # resposta HTTP + handshake TLS
nc -zv host 5432               # a porta 5432 está aberta/alcançável?
ss -tulpn                      # portas ouvindo nesta máquina
nslookup host / dig host       # resolução DNS
```

Erros frequentes: DNS falhando, *security group*/firewall bloqueando a porta,
credencial/token expirado, *timeout* por rede lenta.

## Padrões de falha típicos em pipelines (e sintomas)

| Sintoma | Causas prováveis |
| --- | --- |
| Job "sumiu" sem erro claro | OOM killer (`journalctl -k`), container morto |
| "No space left on device" | disco cheio (`df -h`) ou inodes (`df -i`) |
| "Permission denied" | permissões de arquivo/dir, usuário do container |
| Lento de repente | skew/volume de dados, I/O, *shuffle*, índice faltando |
| "Connection refused/timeout" | serviço fora, porta/firewall, DNS, credencial |
| Dados errados, sem erro | bug de lógica/idempotência, schema mudou na origem |
| Falha intermitente | rede instável, dependência externa, *race condition* |

## Dados corretos mas "errados": o pior tipo

Quando o job "passou" mas o número está errado, logs do SO não ajudam. Vá para:

- [Data quality](../../12-data-quality/README.md) — testes e validações.
- [Observabilidade de dados](../../24-observability/06-data-freshness/README.md) —
  *freshness*, volume, distribuição.
- [Lineage](../../27-data-catalog-metadata/02-lineage-column-lineage/README.md) —
  rastrear a coluna até a origem.

## Boas práticas de logging (para facilitar o futuro)

- Logue com **timestamp, nível e contexto** (qual tabela/partição/execução).
- Mensagens **acionáveis**: diga o quê, onde e, se possível, o porquê.
- Separe `stdout` (dados/resultado) de `stderr` (logs).
- Prefira **logs estruturados** (JSON) em produção — fáceis de filtrar/agregar.
- Não logue segredos nem PII (ver [security](../../26-security/07-data-masking-pii/README.md)).

## Erros comuns

- Ler só a última linha do erro e ignorar o *traceback*.
- Esquecer de checar disco/memória antes de culpar o código.
- Mudar várias coisas de uma vez ao depurar (impossível saber o que resolveu).
- Não registrar a causa raiz → o mesmo incidente volta.

## Relação com outros conceitos

- Usa [processos](../03-processes-and-permissions/README.md) e
  [processamento de texto](../04-text-processing/README.md).
- Escala para [observabilidade](../../24-observability/README.md) e
  [incident response](../../24-observability/07-incident-response/README.md).

## Exercícios

1. Um job de ETL "morreu" sem mensagem. Descreva, passo a passo, como você
   investigaria (comandos específicos).
2. Uma escrita falha com "No space left on device" mas `df -h` mostra espaço.
   Qual o próximo comando e por quê?
3. Um consumidor não conecta no Kafka. Liste 4 verificações de rede em ordem.
4. Projete o formato de log (campos) ideal para um pipeline de ingestão diária.

## Referências

- `man journalctl`, `man ss`, `man top`.
- Google SRE Book — capítulos sobre troubleshooting (gratuito online).
- Brendan Gregg — materiais de performance/observabilidade de Linux.
