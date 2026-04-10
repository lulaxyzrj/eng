{{ config(materialized='table') }}

{%- set datepart = "day" -%}
{%- set start_date = "DATE('2024-01-01')" -%}
{%- set end_date = "DATE('2024-12-31')" -%}

WITH as_of_date AS (
    {{ dbt_utils.date_spine(datepart=datepart,
                            start_date=start_date,
                            end_date=end_date) }}
)

SELECT DATE_DAY AS AS_OF_DATE FROM as_of_date