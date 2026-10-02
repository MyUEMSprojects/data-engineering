# Graph databases

> 🔵 Core · Parte de [NoSQL](../README.md)

## O que é

Bancos de dados que modelam dados como um **grafo**: **nós** (entidades) conectados por
**arestas** (relacionamentos), ambos podendo ter propriedades. São otimizados para
consultar **relacionamentos** — "amigos de amigos", "caminho entre A e B", "quem
influencia quem". Exemplos: **Neo4j**, **Amazon Neptune**, **ArangoDB**, **JanusGraph**.

## Por que existe / que problema resolve

Alguns domínios são, por natureza, redes de relacionamentos: redes sociais, detecção de
fraude, recomendação, grafos de conhecimento, logística, [lineage de dados](../../../27-data-catalog-metadata/02-lineage-column-lineage/README.md).
Em um relacional, consultar relacionamentos profundos exige muitos **joins** recursivos
— lento e ilegível. Grafos tornam isso natural e eficiente.

## Como funciona

Modelo *property graph*:

```text
(Ana:Pessoa {idade:30}) -[:AMIGO_DE {desde:2020}]-> (Bob:Pessoa)
(Bob) -[:COMPROU]-> (Produto {nome:"X"})
```

- **Nós** têm rótulos (`:Pessoa`) e propriedades.
- **Arestas** têm tipo (`:AMIGO_DE`), direção e propriedades.
- **Index-free adjacency** — cada nó referencia diretamente seus vizinhos, então
  "atravessar" uma relação é O(1), independente do tamanho total do grafo. É o que torna
  travessias profundas rápidas.

## Linguagens de consulta

**Cypher** (Neo4j) descreve padrões de grafo visualmente:

```cypher
// amigos de amigos da Ana que ela ainda não conhece
MATCH (ana:Pessoa {nome:'Ana'})-[:AMIGO_DE]->(amigo)-[:AMIGO_DE]->(sugestao)
WHERE NOT (ana)-[:AMIGO_DE]->(sugestao) AND sugestao <> ana
RETURN DISTINCT sugestao.nome
```

```cypher
// caminho mais curto entre duas pessoas
MATCH p = shortestPath((a:Pessoa {nome:'Ana'})-[:AMIGO_DE*]-(b:Pessoa {nome:'Carol'}))
RETURN p
```

Outras linguagens: **Gremlin** (Apache TinkerPop), **SPARQL** (grafos RDF),
**GQL** (padrão ISO recente).

## A vantagem sobre joins relacionais

A consulta "amigos de amigos de amigos" (3 níveis) num relacional é um self-join
triplo que piora exponencialmente com a profundidade. No grafo, é uma travessia que
custa proporcional ao número de conexões percorridas, não ao tamanho total da tabela —
diferença enorme em grafos grandes e densos.

## Casos de uso

- **Detecção de fraude** — anéis de fraude são padrões de grafo (contas compartilhando
  dispositivos/endereços).
- **Recomendação** — "quem comprou isto também comprou".
- **Redes sociais** — conexões, influência, comunidades.
- **Grafos de conhecimento** — entidades e suas relações.
- **Lineage/impact analysis** — o próprio [data lineage](../../../27-data-catalog-metadata/02-lineage-column-lineage/README.md)
  é um grafo.
- **Logística/rotas** — caminhos ótimos.

## Vantagens

- Consultas de relacionamento profundas e naturais.
- Performance constante na travessia (index-free adjacency).
- Modelo expressivo e intuitivo para dados conectados.

## Limitações / trade-offs

- **Nicho**: ruim para cargas tabulares/analíticas gerais.
- Escala horizontal é difícil (particionar um grafo sem cortar muitas arestas é um
  problema duro).
- Ecossistema/ferramental menor que relacionais.
- Analytics agregado tradicional é melhor num warehouse.

## Quando usar / quando NÃO usar

- **Use** quando a pergunta central é sobre **relacionamentos/caminhos/padrões de
  conexão** e a profundidade importa.
- **NÃO use** como banco de propósito geral ou para analytics tabular agregado — ali o
  relacional/warehouse vence.

## O ângulo do DE

- Pode ser **fonte** (ingerir para o lake) ou **destino especializado** (construir um
  grafo a partir de dados do warehouse para análise de rede).
- Lineage de dados e catálogos (ex.: [DataHub](../../../27-data-catalog-metadata/04-tools/README.md))
  internamente são grafos.
- Construir *features* de grafo (centralidade, comunidades) para ML é um caso
  crescente.

## Erros comuns

- Usar grafo para dados que são tabulares (overkill e pior performance).
- Esperar escalar horizontalmente como um key-value.
- Modelar tudo como nó/aresta sem necessidade real de travessia.

## Boas práticas

- Use grafo quando a travessia de relacionamentos é o padrão de acesso dominante.
- Modele tipos de nó/aresta e propriedades com clareza.
- Para analytics agregado, combine com warehouse (não force no grafo).

## Relação com outros conceitos

- [Data lineage](../../../27-data-catalog-metadata/02-lineage-column-lineage/README.md)
  é modelado como grafo.
- Features de grafo para [ML](../../../31-data-engineering-and-ml/README.md).
- Comparar com joins recursivos em [SQL/CTEs](../../../05-sql/04-subqueries-ctes/README.md).

## Exercícios

1. Modele uma mini rede social (pessoas, amizades, compras) como property graph.
2. Escreva (em Cypher) a recomendação "amigos de amigos" e o caminho mais curto entre
   duas pessoas.
3. Explique por que "amigos de amigos de amigos" é caro em SQL e barato no grafo.
4. Dê um exemplo de detecção de fraude expressa como padrão de grafo.

## Referências

- Documentação do Neo4j (neo4j.com/docs) e Cypher.
- Robinson, Webber, Eifrem. *Graph Databases*. O'Reilly.
- Apache TinkerPop (Gremlin); padrão GQL (ISO/IEC 39075).
