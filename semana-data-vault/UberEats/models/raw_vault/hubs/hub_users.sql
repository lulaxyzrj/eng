{{ config(
    materialized = 'incremental',
    unique_key = 'hash_hub_cpf'
) }}

WITH combined_sources AS (
  SELECT cpf, load_dts
  FROM {{ source('uber_eats', 'v_stg_users_mssql') }}
  WHERE cpf IS NOT NULL

  UNION ALL

  SELECT cpf, load_dts
  FROM {{ source('uber_eats', 'v_stg_users_mongodb') }}
  WHERE cpf IS NOT NULL
),

deduplicated AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key(['cpf']) }} AS hash_hub_cpf,
    -- ['multi_tenant_id', 'cpf']
    cpf,
    'trn-user' AS bkcc,
    'tenant-br' AS multi_tenant_id,
    MIN(load_dts) AS load_dts,
    'dbt' AS record_source
  FROM combined_sources
  GROUP BY cpf
)

SELECT *
FROM deduplicated

{% if is_incremental() %}
WHERE hash_hub_cpf NOT IN (
  SELECT hash_hub_cpf FROM {{ this }}
)
{% endif %}
