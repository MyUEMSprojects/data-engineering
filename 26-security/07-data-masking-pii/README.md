# Mascaramento de dados e PII

> 🟣 Production · Parte de [26 — Security](../README.md)

> ⚠️ Conteúdo educacional; consulte jurídico/DPO para decisões de conformidade.

## O que é

**PII (Personally Identifiable Information)** é qualquer informação que identifica — direta ou
indiretamente — uma pessoa. No Brasil, a LGPD usa **"dado pessoal"** (e **"dado pessoal sensível"** para
categorias de maior risco) — ver [LGPD](../08-lgpd/README.md). **Mascaramento e técnicas relacionadas**
reduzem a exposição dessas informações mantendo (quando possível) a utilidade dos dados.

## Tipos de dados a proteger

| Categoria | Exemplos |
| --- | --- |
| **Identificadores diretos** | nome, **CPF**, RG, e-mail, telefone, endereço, foto |
| **Identificadores indiretos / quase-identificadores** | CEP, data de nascimento, gênero, cargo, IP, device ID, geolocalização — **combinados** podem reidentificar |
| **Sensíveis (LGPD)** | saúde, biometria, genético, origem racial/étnica, religião, opinião política, vida sexual, filiação sindical |
| **Financeiros** | cartão (PCI-DSS), conta, renda |
| **Credenciais** | senhas, tokens (tratados em [secrets](../04-secrets-management/README.md)) |

> Atenção aos **quase-identificadores**: remover o nome não anonimiza — CEP + data de nascimento + gênero
> identificam muita gente.

## Técnicas (do reversível ao irreversível)

| Técnica | O que faz | Reversível? | Uso típico |
| --- | --- | --- | --- |
| **Mascaramento (masking)** | oculta parcialmente (`***.***.123-45`, `a***@x.com`) | não (visão) | exibição a usuários sem necessidade do valor completo |
| **Hashing** (com salt/HMAC) | substitui por hash determinístico | não (mas pode ser "adivinhado" por dicionário se espaço pequeno) | **join/dedupe sem expor** o valor; use HMAC com chave p/ resistir a dicionário |
| **Tokenização** | substitui por token aleatório; mapeamento num **cofre** isolado | sim (via cofre) | cartão, CPF; reduz escopo PCI/LGPD |
| **Pseudonimização** | troca identificadores por pseudônimos (token/hash) mantendo vínculo | sim, com informação adicional guardada à parte | analytics/ML mantendo consistência por titular; **ainda é dado pessoal** (LGPD) |
| **Criptografia de campo** | cifra o valor ([encryption](../03-encryption/README.md)) | sim (com chave) | proteger PII em repouso; só quem tem a chave lê |
| **Generalização** | reduz precisão (idade 34 → faixa 30–39; CEP → 3 dígitos) | não | analytics, publicar estatísticas |
| **Supressão/remoção** | exclui o campo | não | minimização |
| **Perturbação/ruído** | altera valores levemente | não | estatísticas; **privacidade diferencial** |
| **Dados sintéticos** | gera dados artificiais com distribuição similar | n/a | dev/teste/ML |
| **Embaralhamento (shuffling)** | troca valores entre linhas | não | testes |

### Mascaramento estático vs dinâmico

- **Estático** — transforma os dados **na cópia** (ex.: gerar dataset mascarado para staging/dev). Irreversível
  naquela cópia; ótimo para **ambientes não-produtivos**.
- **Dinâmico (DDM)** — aplicado **na consulta**, conforme quem pergunta: a mesma coluna aparece **mascarada
  para o analista** e **completa para o time de fraude**, sem duplicar dados. Implementado em warehouses
  (Snowflake masking policies, BigQuery policy tags/`DATA MASKING`, Redshift, Databricks/Unity Catalog column
  masks) — **política por tag** de classificação ([classificação](../../25-data-governance/05-access-control-classification/README.md)).

```sql
-- Snowflake (conceitual): política de mascaramento por papel
create masking policy mask_cpf as (v string) returns string ->
  case when current_role() in ('FRAUDE','DPO') then v
       else regexp_replace(v, '\\d(?=\\d{2})', '*') end;
alter table clientes modify column cpf set masking policy mask_cpf;
```

## Anonimização vs pseudonimização (LGPD)

- **Anonimização** — dado que **não permite identificar** o titular por meios razoáveis; **deixa de ser
  dado pessoal** (fora do escopo da LGPD). Difícil de atingir de verdade — risco de **reidentificação**
  (ataques de ligação com outras bases).
- **Pseudonimização** — o dado só identifica com **informação adicional mantida separada**; **continua sendo
  dado pessoal** e sujeito à LGPD, mas reduz risco.

Medidas para anonimização robusta: **k-anonimato**, **l-diversidade**, **t-proximidade**, **privacidade
diferencial**; testar risco de reidentificação.

## Onde aplicar na plataforma de dados

```text
Ingestão ─► [pseudonimizar/segregar PII cedo] ─► bronze restrito ─► silver (PII tokenizada/mascarada) ─► gold (agregado/anonimizado) ─► BI/ML
                                  └─ cofre/tabela de mapeamento titular↔token (acesso mínimo, auditado)
```

- **Cedo**: minimize PII logo na ingestão; **segregue** PII em schemas/tabelas restritas (facilita acesso,
  retenção e exclusão — [retenção](../../25-data-governance/06-retention-auditing/README.md)).
- **Camadas**: raw/bronze com acesso muito restrito; silver/gold com PII mascarada/tokenizada; marts
  públicos/internos **agregados**.
- **Ambientes**: **nunca** PII real em dev/teste/CI — use sintéticos ou mascarados estaticamente
  ([ambientes](../../23-cicd-dataops/04-environments-artifacts/README.md)).
- **ML**: features sem identificadores diretos; atenção a vazamento por quase-identificadores e a
  viés/não discriminação ([DE + ML](../../31-data-engineering-and-ml/README.md)).
- **Logs/notebooks/exports**: não logar PII; cuidado com extratos soltos ([logging](../../24-observability/01-logging/README.md)).

## Descoberta e classificação de PII

Você não protege o que não encontra: **scanners automáticos** (Macie, DLP API, Purview, classificadores do
DataHub/OpenMetadata) detectam padrões (CPF, e-mail, cartão) e geram **tags** que acionam políticas
([classificação](../../25-data-governance/05-access-control-classification/README.md)). Revise falsos
positivos/negativos; use **lineage** para propagar a classificação a derivados
([lineage](../../25-data-governance/03-lineage/README.md)).

## Exemplos práticos (Python)

```python
import hmac, hashlib

def pseudonimizar(valor: str, chave: bytes) -> str:
    # HMAC com chave secreta: determinístico (permite join) e resistente a dicionário
    return hmac.new(chave, valor.encode(), hashlib.sha256).hexdigest()

def mascara_cpf(cpf: str) -> str:
    d = "".join(c for c in cpf if c.isdigit())
    return f"***.***.{d[6:9]}-**" if len(d) == 11 else "***"
```

> A `chave` vem do [secret manager](../04-secrets-management/README.md); sem a chave, não se reverte nem se
> adivinha por dicionário.

## Trade-offs

- **Utilidade × privacidade**: quanto mais protegido, menos preciso/útil (generalização reduz análise fina).
- **Determinístico** (mesmo valor → mesmo token) permite joins/dedupe, mas facilita ataques de inferência;
  **aleatório** é mais seguro, porém quebra joins.
- **Reversibilidade** exige proteger muito bem o cofre/chaves.
- **Desempenho/complexidade** de DDM e tokenização.

## Erros comuns

- Achar que remover o nome (ou hash simples de CPF sem chave) anonimiza.
- Hash sem salt/chave de espaço pequeno (CPF tem ~10⁹ combinações → quebra por força bruta).
- PII real em dev/teste/logs/notebooks/planilhas.
- Mascarar só na camada de BI e deixar PII em claro nas camadas inferiores acessíveis.
- Ignorar quase-identificadores e a reidentificação por combinação.
- Tabela de mapeamento titular↔token com acesso amplo.
- Classificação manual/desatualizada; derivados sem herdar a tag.

## Boas práticas

- Minimize e segregue PII cedo; proteja em camadas; **tag + política** de mascaramento dinâmico.
- Pseudonimização com **HMAC/tokenização** (chave/cofre protegidos); anonimização testada contra
  reidentificação.
- Sem PII real fora de produção; sintéticos/mascarados estáticos.
- Descoberta automática + lineage para propagar classificação; auditoria de acesso a PII.

## Relação com outros conceitos

- [LGPD](../08-lgpd/README.md), [criptografia](../03-encryption/README.md),
  [menor privilégio](../06-least-privilege/README.md),
  [classificação/acesso](../../25-data-governance/05-access-control-classification/README.md),
  [compliance](../../25-data-governance/07-compliance-privacy/README.md), [retenção](../../25-data-governance/06-retention-auditing/README.md).

## Exercícios

1. Classifique 10 colunas de uma tabela de clientes (direto, quase-identificador, sensível) e escolha a
   técnica para cada.
2. Explique por que `sha256(cpf)` sem chave é fraco e como melhorar (HMAC/tokenização).
3. Desenhe uma política de mascaramento dinâmico por tag para 3 papéis distintos.
4. Gere um dataset sintético/mascarado de clientes para uso em staging.

## Referências

- LGPD (arts. 5º, 12, 13); guias da ANPD sobre anonimização; ISO/IEC 20889 (de-identificação);
  Dwork & Roth, *The Algorithmic Foundations of Differential Privacy*; docs de masking policies
  (Snowflake/BigQuery/Unity Catalog).
