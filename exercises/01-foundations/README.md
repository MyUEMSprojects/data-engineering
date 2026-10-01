# Exercícios — Módulo 01: Fundamentos

Teoria em [01-foundations](../../01-foundations/README.md) · [índice de exercícios](../README.md)

## 1. 🟢 Conceitual — OLTP ou OLAP?

Classifique cada carga como **OLTP** ou **OLAP** e diga a característica que decide: (a) "registrar o pagamento do pedido 123";
(b) "receita por país por mês nos últimos 3 anos"; (c) "atualizar o endereço de um cliente"; (d) "top 10 produtos por categoria".

<details><summary>Gabarito</summary>

(a) **OLTP** — escrita pontual, transacional, baixa latência. (b) **OLAP** — varre muitas linhas e agrega. (c) **OLTP** — atualização por chave.
(d) **OLAP** — agregação + ordenação sobre grande volume. O que decide é o **padrão de acesso** (poucas linhas por chave × muitas linhas agregadas),
que por sua vez leva a armazenamento por linha (OLTP) ou por coluna (OLAP). Ver [OLTP vs OLAP](../../01-foundations/07-oltp-vs-olap/README.md).
</details>

## 2. 🟢 Conceitual — As etapas do ciclo de vida

Ordene e nomeie as etapas do ciclo de vida do dado e dê **um exemplo de ferramenta** para cada: *consumo, armazenamento, geração, transformação, ingestão, serviço*.

<details><summary>Gabarito</summary>

**Geração** (app/sensor) → **Ingestão** (Kafka, Fivetran, scripts) → **Armazenamento** (S3, PostgreSQL, warehouse) → **Transformação** (dbt, Spark) →
**Serviço** (BI, API, feature store) → **Consumo** (dashboards, ML, relatórios). O armazenamento é uma **corrente transversal** que toca todas as etapas.
Ver [ciclo de vida](../../01-foundations/03-data-lifecycle/README.md).
</details>

## 3. 🔵 Conceitual — Batch ou streaming?

Para cada requisito, escolha batch, micro-batch ou streaming **e justifique com a latência exigida e o custo**: (a) fechamento financeiro diário;
(b) detecção de fraude em cartão antes de aprovar a compra; (c) dashboard de operações atualizado a cada 5 minutos; (d) recálculo mensal de comissões.

<details><summary>Gabarito</summary>

(a) **batch** — latência de horas é aceitável, reprocessável e barato. (b) **streaming** — decisão em milissegundos, antes da resposta ao cliente.
(c) **micro-batch** (ou streaming simples) — minutos bastam; micro-batch tem menor complexidade operacional. (d) **batch** — periodicidade mensal.
Regra prática: **comece pelo mais simples que atende o requisito de latência**; streaming custa mais (estado, ordem, reprocessamento).
Ver [batch vs streaming](../../01-foundations/06-batch-vs-streaming/README.md).
</details>

## 4. 🔵 Debugging — "Os números não batem"

O painel de vendas mostra **R$ 1,20 mi** e o relatório financeiro **R$ 1,15 mi** para o mesmo mês. Liste **cinco** causas plausíveis, relacionadas a engenharia de dados, e como cada uma seria confirmada.

<details><summary>Gabarito</summary>

1. **Fuso horário/fronteira do mês** (UTC × local) → comparar contagem de pedidos nos últimos/primeiros dias. 2. **Cancelamentos/reembolsos** incluídos em um e não no outro → conferir `status`.
3. **Duplicatas** na ingestão (*at-least-once*) → `count(*)` × `count(distinct id)`. 4. **Dado tardio** (o painel foi calculado antes de chegar tudo) → comparar por data de ingestão.
5. **Definições diferentes de "venda"** (bruto × líquido, com/sem frete) → contrato/definição de métrica. Moral: métrica sem **definição única e testada** gera discussões — ver [data contracts](../../29-data-contracts/README.md).
</details>

## 5. 🟣 Arquitetura — Do requisito ao desenho

Uma startup de entregas quer: (i) rastrear pedidos em tempo real no app; (ii) um relatório diário de desempenho por região; (iii) treinar um modelo de previsão de atraso.
Desenhe a arquitetura de dados (fontes, ingestão, armazenamento, processamento, consumo) e justifique **três** decisões e **dois** riscos.

<details><summary>Gabarito (um caminho possível)</summary>

Fontes: banco OLTP do app + eventos GPS. **Ingestão:** CDC/Debezium do OLTP e eventos em Kafka. **Armazenamento:** lake (bronze/silver/gold) em object storage + warehouse para BI.
**Processamento:** streaming leve para o rastreio (estado por pedido), batch diário (dbt/Spark) para o relatório; *feature store* para o modelo. **Decisões:** (1) CDC em vez de consultar o OLTP (não derruba o app);
(2) lake + warehouse (custo baixo para histórico/ML, SQL rápido para BI); (3) tempo de evento para janelas. **Riscos:** (1) dado tardio/fora de ordem do GPS distorce métricas; (2) vazamento de PII (endereços) — exige mascaramento e acesso mínimo.
Compare com [Projeto 10](../../projects/10-capstone/README.md).
</details>

## 6. 🟣 Conceitual — Teorema CAP na prática

Um sistema de pedidos replica dados entre duas regiões. Durante uma **partição de rede**, o time precisa escolher entre **recusar escritas** ou **aceitar e reconciliar depois**.
Qual é CP e qual é AP? Dê um domínio onde cada escolha é correta e o mecanismo de reconciliação do caso AP.

<details><summary>Gabarito</summary>

Recusar escritas = **CP** (consistência > disponibilidade): correto para **saldo bancário/estoque crítico**. Aceitar e reconciliar = **AP**: correto para **carrinho de compras/curtidas**.
Reconciliação no AP: *last-write-wins* (simples, perde dados), **vector clocks**, **CRDTs** ou regras de negócio (merge de carrinhos). Lembrete: CAP só vale **durante** partições; fora delas a escolha é latência × consistência (PACELC).
Ver [sistemas distribuídos](../../01-foundations/05-distributed-systems-fundamentals/README.md).
</details>
