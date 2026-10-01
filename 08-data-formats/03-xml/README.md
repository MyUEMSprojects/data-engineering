# XML

> 🔵 Core · Parte de [08 — Data Formats](../README.md)

## O que é

**XML (eXtensible Markup Language)** é um formato de texto hierárquico baseado em tags,
com suporte a atributos, namespaces e validação por schema (XSD). Foi o padrão dominante
de troca de dados nos anos 2000, hoje largamente substituído por
[JSON](../02-json-jsonl/README.md), mas ainda muito presente em **sistemas legados**,
integrações governamentais, bancárias, SOAP e certos padrões setoriais.

```xml
<pedido id="1">
  <cliente uf="SP">Ana</cliente>
  <itens>
    <item qtd="2">Produto X</item>
    <item qtd="1">Produto Y</item>
  </itens>
</pedido>
```

## Por que o DE ainda precisa

Você não vai *escolher* XML para um projeto novo, mas vai **ingeri-lo** de fontes legadas:
notas fiscais eletrônicas (NF-e no Brasil), sistemas financeiros, EDI, feeds SOAP, certos
exports corporativos. Saber extrair dados de XML de forma robusta é uma necessidade
prática.

## Características

- **Hierárquico** — elementos aninhados, como JSON, mas mais verboso.
- **Atributos vs elementos** — dados podem estar em atributos (`id="1"`) ou em elementos
  filhos; a mesma informação pode ser modelada de formas diferentes (fonte de confusão).
- **Namespaces** — prefixos (`ns:tag`) para evitar colisão de nomes (complicam o parsing).
- **Schema (XSD)** — valida a estrutura; **DTD** é a forma antiga.
- **Verboso** — tags de abertura/fechamento inflam o tamanho vs JSON/binários.

## Parsing em Python

```python
import xml.etree.ElementTree as ET

tree = ET.parse("pedido.xml")
root = tree.getroot()
for item in root.findall(".//item"):
    print(item.get("qtd"), item.text)      # atributo e texto
```

- `ElementTree` (stdlib) resolve o básico.
- **`lxml`** é mais rápido e suporta XPath completo/validação XSD.
- Para arquivos **grandes**, use parsing **em streaming** (`iterparse`) para não carregar
  tudo na memória:

```python
for event, elem in ET.iterparse("grande.xml", events=("end",)):
    if elem.tag == "pedido":
        processar(elem)
        elem.clear()        # libera memória do elemento processado
```

## XPath (consultar XML)

Linguagem para navegar/selecionar nós (com `lxml`):

```python
from lxml import etree
doc = etree.parse("pedido.xml")
doc.xpath("//item[@qtd>1]/text()")      # itens com qtd > 1
```

## Segurança: ataques por XML

XML tem vetores de ataque famosos que o DE deve conhecer ao ingerir XML de terceiros:

- **XXE (XML External Entity)** — entidades externas podem ler arquivos locais/fazer SSRF.
- **Billion laughs** — entidades recursivas que explodem a memória (DoS).

Mitigue: **desabilite resolução de entidades externas/DTD** no parser (use
`defusedxml` em Python, ou configure `lxml` com `resolve_entities=False`,
`no_network=True`). **Nunca** parseie XML não confiável com configuração padrão insegura.

## Converter XML → tabular/JSON

O fluxo típico de ingestão: parsear o XML, **achatar** a hierarquia (explodindo listas de
elementos em linhas, como no [JSON aninhado](../02-json-jsonl/README.md)) e gravar em
[Parquet](../04-parquet/README.md). Decisões: como mapear atributos vs elementos, como
lidar com namespaces, o que fazer com elementos opcionais/repetidos.

## XML vs JSON

| | XML | JSON |
| --- | --- | --- |
| Verbosidade | alta (tags) | menor |
| Atributos | sim | não (só chaves) |
| Namespaces | sim | não |
| Schema | XSD (maduro) | JSON Schema |
| Uso hoje | legado/governo/SOAP | APIs modernas |

## Erros comuns

- Parsear XML grande carregando tudo na memória (use `iterparse`).
- Ignorar **namespaces** e não encontrar os nós.
- Confundir dados em atributos vs elementos.
- Parsear XML não confiável sem proteção contra XXE/billion laughs.
- Tratar XML por regex/string (frágil — use um parser real).

## Boas práticas

- Use `lxml`/`defusedxml`; `iterparse` para grandes volumes.
- Trate namespaces explicitamente; valide com XSD quando disponível.
- Desabilite entidades externas ao ingerir de terceiros.
- Converta para formato tabular/colunar nas camadas refinadas.

## Relação com outros conceitos

- Ingestão de [fontes legadas](../../09-etl-elt/02-ingestion-extraction/README.md).
- Achatamento semelhante ao de [JSON aninhado](../02-json-jsonl/README.md).
- Segurança: [26 — Security](../../26-security/README.md).

## Exercícios

1. Extraia todos os `item` (qtd e descrição) de um XML de pedidos com namespaces.
2. Processe um XML grande com `iterparse` liberando memória por elemento.
3. Converta um XML hierárquico em tabela achatada e grave em Parquet.
4. Explique XXE e como configurar o parser para evitá-lo.

## Referências

- W3C XML 1.0; documentação de `xml.etree.ElementTree`, `lxml`, `defusedxml`.
- OWASP — XML External Entity (XXE) Prevention.
