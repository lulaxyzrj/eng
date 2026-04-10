{{ config(
    materialized = 'incremental',
    unique_key = 'hash_hub_cnpj'
) }}

WITH source AS (
  SELECT
    cnpj,
    load_dts,
    rec_src AS record_source,
    {{ dbt_utils.generate_surrogate_key(['cnpj']) }} AS hash_hub_cnpj
  FROM {{ source('uber_eats', 'v_stg_restaurants') }}
),

deduplicated AS (
  SELECT DISTINCT
    hash_hub_cnpj,
    cnpj,
    'trn-restaurant' AS bkcc,
    'tenant-br' AS multi_tenant_id,
    load_dts,
    record_source
  FROM source
)

SELECT *
FROM deduplicated

{% if is_incremental() %}
WHERE hash_hub_cnpj NOT IN (
  SELECT hash_hub_cnpj FROM {{ this }}
)
{% endif %}
