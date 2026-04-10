{{ config(
    materialized = 'incremental',
    unique_key = ['hash_hub_order_id', 'load_dts']
) }}

WITH source AS (
  SELECT
    order_id,
    status_name,
    status_timestamp,
    status_id,
    load_dts,
    rec_src AS record_source
  FROM {{ source('uber_eats', 'v_stg_status') }}
  WHERE order_id IS NOT NULL
),

prepared AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key(['order_id']) }} AS hash_hub_order_id,

    status_name,
    status_timestamp,
    status_id,

    SHA2(
      CONCAT_WS('|',
        COALESCE(TRIM(status_name), ''),
        COALESCE(TO_VARCHAR(status_timestamp), ''),
        COALESCE(TO_VARCHAR(status_id), '')
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
