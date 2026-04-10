{{- config(
    materialized='incremental',
    tags=['raw_vault', 'satellite']
) -}}

WITH source_data AS (
    SELECT DISTINCT
        ORDER_DRIVER_HK,
        ORDER_HK,
        DRIVER_HK,
        LOAD_DTS AS START_DATE,
        CAST('9999-12-31' AS DATE) AS END_DATE,
        EFFECTIVE_FROM,
        LOAD_DTS,
        CAST('9999-12-31' AS DATE) AS LOAD_END_DTS,
        RECORD_SOURCE
    FROM {{ ref('stg_orders') }}
)

SELECT
    ORDER_DRIVER_HK,
    ORDER_HK,
    DRIVER_HK,
    START_DATE,
    END_DATE,
    EFFECTIVE_FROM,
    LOAD_DTS,
    LOAD_END_DTS,
    RECORD_SOURCE
FROM source_data

{% if is_incremental() %}
WHERE LOAD_DTS > (SELECT MAX(LOAD_DTS) FROM {{ this }})
{% endif %}