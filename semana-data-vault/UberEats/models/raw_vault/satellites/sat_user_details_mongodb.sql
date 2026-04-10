{{ config(
    materialized = 'incremental',
    unique_key = ['hash_hub_cpf', 'load_dts']
) }}

WITH source AS (
  SELECT
    cpf,
    user_id,
    city,
    email,
    delivery_address,
    phone_number,
    country,
    load_dts,
    rec_src AS record_source
  FROM {{ source('uber_eats', 'v_stg_users_mongodb') }}
  WHERE cpf IS NOT NULL
),

prepared AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key(['cpf']) }} AS hash_hub_cpf,

    user_id,
    city,
    email,
    delivery_address,
    phone_number,
    country,

    SHA2(
      CONCAT_WS('|',
        COALESCE(TRIM(user_id), ''),
        COALESCE(TRIM(city), ''),
        COALESCE(TRIM(email), ''),
        COALESCE(TRIM(delivery_address), ''),
        COALESCE(TRIM(phone_number), ''),
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
