{{ config(
    materialized = 'incremental',
    unique_key = ['hash_hub_cpf', 'load_dts']
) }}

WITH source AS (
  SELECT
    cpf,
    user_id,
    first_name,
    last_name,
    birthday,
    job,
    phone_number,
    company_name,
    country,
    load_dts,
    rec_src AS record_source
  FROM {{ source('uber_eats', 'v_stg_users_mssql') }}
  WHERE cpf IS NOT NULL
),

prepared AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key(['cpf']) }} AS hash_hub_cpf,

    user_id,
    first_name,
    last_name,
    birthday,
    job,
    phone_number,
    company_name,
    country,

    SHA2(
      CONCAT_WS('|',
        COALESCE(TRIM(user_id), ''),
        COALESCE(TRIM(first_name), ''),
        COALESCE(TRIM(last_name), ''),
        COALESCE(TO_VARCHAR(birthday), ''),
        COALESCE(TRIM(job), ''),
        COALESCE(TRIM(phone_number), ''),
        COALESCE(TRIM(company_name), ''),
        COALESCE(TRIM(country), '')
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
  WHERE (hash_hub_cpf, hash_diff) NOT IN (
    SELECT hash_hub_cpf, hash_diff
    FROM {{ this }}
  )
  {% endif %}
)

SELECT *
FROM deduplicated
