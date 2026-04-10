{{ config(
    materialized = 'incremental',
    unique_key = ['hash_hub_order_id', 'load_dts']
) }}

WITH source AS (
  SELECT
    order_id,
    order_date,
    total_amount,
    payment_key,
    load_dts,
    rec_src AS record_source
  FROM {{ source('uber_eats', 'v_stg_orders') }}
  WHERE order_id IS NOT NULL
),

prepared AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key(['order_id']) }} AS hash_hub_order_id,

    order_date,
    total_amount,
    payment_key,

    SHA2(
      CONCAT_WS('|',
        COALESCE(TO_VARCHAR(order_date), ''),
        COALESCE(TO_VARCHAR(total_amount), ''),
        COALESCE(TRIM(payment_key), '')
      ), 256
    ) AS hash_diff,

    'tenant-br' AS multi_tenant_id,
    load_dts,
    record_source
  FROM source
),

deduplicated AS (
  SELECT *
  FROM prepared
  {% if is_incremental() %}
  WHERE (hash_hub_order_id, hash_diff) NOT IN (
    SELECT hash_hub_order_id, hash_diff
    FROM {{ this }}
  )
  {% endif %}
)

SELECT *
FROM deduplicated
