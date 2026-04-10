{{ config(
    materialized = 'incremental',
    unique_key = 'hash_hub_order_id'
) }}

WITH source AS (
  SELECT
    order_id,
    load_dts,
    rec_src AS record_source,
    {{ dbt_utils.generate_surrogate_key(['order_id']) }} AS hash_hub_order_id
  FROM {{ source('uber_eats', 'v_stg_orders') }}
),

deduplicated AS (
  SELECT DISTINCT
    hash_hub_order_id,
    order_id,
    'trn-order' AS bkcc,
    'tenant-br' AS multi_tenant_id,
    load_dts,
    record_source
  FROM source
)

SELECT *
FROM deduplicated

{% if is_incremental() %}
WHERE hash_hub_order_id NOT IN (
  SELECT hash_hub_order_id FROM {{ this }}
)
{% endif %}
