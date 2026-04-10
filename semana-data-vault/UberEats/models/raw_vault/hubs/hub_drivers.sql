{{ config(
    materialized = 'incremental',
    unique_key = 'hash_hub_license_number'
) }}

WITH source AS (
  SELECT
    license_number,
    load_dts,
    rec_src AS record_source,
    {{ dbt_utils.generate_surrogate_key(['license_number']) }} AS hash_hub_license_number
  FROM {{ source('uber_eats', 'v_stg_drivers') }}
),

deduplicated AS (
  SELECT DISTINCT
    hash_hub_license_number,
    license_number,
    'trn-driver' AS bkcc,
    'tenant-br' AS multi_tenant_id,
    load_dts,
    record_source
  FROM source
)

SELECT *
FROM deduplicated

{% if is_incremental() %}
WHERE hash_hub_license_number NOT IN (
  SELECT hash_hub_license_number FROM {{ this }}
)
{% endif %}
