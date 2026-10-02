# Exercícios — Módulo 29: Data contracts

Teoria em [29-data-contracts](../../29-data-contracts/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — O que é um contrato de dados

Cite quatro elementos de um contrato e quem são as partes.

<details><summary>Gabarito</summary>

Partes: **produtor** e **consumidor(es)**. Elementos: **schema** (campos/tipos/nulos), **semântica** (definições, unidades), **qualidade** (checks), **SLA/frescor**, **dono**, política de **versionamento/depreciação**. Ver [conceito](../../29-data-contracts/01-concept/README.md).
</details>

## 2. 🟢 Conceitual — Mudança compatível?

Classifique como compatível (✓) ou **quebra** (✗): adicionar campo opcional; renomear `amount` para `total`; mudar `int` para `string`; remover campo não usado; apertar um domínio (`status` perde um valor).

<details><summary>Gabarito</summary>

✓ adicionar campo opcional. ✗ renomear. ✗ mudar tipo. ✗ remover (se qualquer consumidor usa; "não usado" precisa ser **provado** pela linhagem). ✗ apertar domínio pode quebrar produtores/consumidores conforme o sentido. Ver [compatibilidade](../../29-data-contracts/04-compatibility-versioning/README.md).
</details>

## 3. 🔵 Implementação — Contrato executável

Escreva um contrato YAML (schema + 2 regras de qualidade + SLA) e uma função que **valida um lote** contra ele.

<details><summary>Gabarito</summary>

```yaml
dataset: orders
version: 1.0.0
owner: pedidos@empresa.com
schema:
  - {name: order_id, type: string, required: true, unique: true}
  - {name: amount, type: decimal, required: true, min: 0}
sla: {freshness_hours: 26}
```

```python
def validate(rows, contract):
    errs = []
    for col in contract["schema"]:
        vals = [r.get(col["name"]) for r in rows]
        if col.get("required") and any(v is None for v in vals): errs.append(f"{col['name']}: nulo")
        if col.get("unique") and len(set(vals)) != len(vals): errs.append(f"{col['name']}: duplicado")
        if "min" in col and any(v is not None and v < col["min"] for v in vals): errs.append(f"{col['name']}: < {col['min']}")
    return errs
```

Versão completa (hard/soft, limites, quarentena): [Projeto 04](../../projects/04-data-quality/README.md). Ver [implementação](../../29-data-contracts/06-implementation/README.md).
</details>

## 4. 🔵 Debugging — O consumidor quebrou

O produtor "só renomeou uma coluna" e três dashboards quebraram. Que **processo e automação** teriam evitado?

<details><summary>Gabarito</summary>

Contrato **versionado** com verificação de compatibilidade **no CI do produtor** (a mudança é rejeitada/avisada), registro de **consumidores** (linhagem) para notificá-los, e período de **depreciação** com duas versões em paralelo. Ver [produtor e consumidor](../../29-data-contracts/03-ownership-producer-consumer/README.md).
</details>

## 5. 🟣 Arquitetura — Enforcement

Onde aplicar o contrato: na **produção** (CI do produtor), na **ingestão** (gate) ou no **consumo** (testes)? Defenda uma combinação.

<details><summary>Gabarito</summary>

Combine: **CI do produtor** (previne), **gate na ingestão** (impede dado ruim de entrar: bloqueia/quarentena) e **testes no consumo** (defesa em profundidade, regras de negócio). Só a primeira *evita* o problema; as outras o *contêm*. Ver [teste de contrato](../../29-data-contracts/05-contract-testing/README.md).
</details>

## 6. 🟣 Arquitetura — Versionamento

Proponha uma política de versionamento semântico para contratos e o ciclo de **depreciação** de uma versão.

<details><summary>Gabarito</summary>

**Patch:** correção de documentação/descrição. **Minor:** adição compatível (campo opcional). **Major:** quebra. Depreciação: anunciar (data + guia de migração), **publicar v1 e v2 em paralelo** por um prazo, monitorar quem ainda lê v1 (linhagem/acessos), então desligar. Registrar tudo no catálogo. Ver [versionamento](../../29-data-contracts/04-compatibility-versioning/README.md).
</details>
