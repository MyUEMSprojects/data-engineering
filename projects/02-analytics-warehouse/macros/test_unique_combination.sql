{# Teste genérico próprio (sem depender de pacotes): a combinação de colunas deve ser única. #}
{% test dbt_utils_free_unique_combination(model, column_names) %}
select {{ column_names | join(', ') }}, count(*) as n
from {{ model }}
group by {{ column_names | join(', ') }}
having count(*) > 1
{% endtest %}
