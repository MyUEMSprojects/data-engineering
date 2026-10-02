with days as (
    select d::date as date_day
    from generate_series(date '2024-01-01', date '2025-12-31', interval '1 day') as d
)
select
    to_char(date_day, 'YYYYMMDD')::int          as date_sk,
    date_day,
    extract(year from date_day)::int            as year,
    extract(quarter from date_day)::int         as quarter,
    extract(month from date_day)::int           as month,
    to_char(date_day, 'YYYY-MM')                as year_month,
    trim(to_char(date_day, 'Day'))              as day_name,
    extract(isodow from date_day)::int          as iso_day_of_week,
    extract(isodow from date_day) in (6, 7)     as is_weekend
from days
