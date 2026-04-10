{{ config(
    materialized = 'incremental',
    unique_key = ['hash_hub_cnpj', 'load_dts']
) }}

WITH source AS (
  SELECT
    cnpj,
    restaurant_id,
    name,
    address,
    city,
    phone_number,
    country,
    cuisine_type,
    opening_time,
    closing_time,
    average_rating,
    num_reviews,
    load_dts,
    rec_src AS record_source
  FROM {{ source('uber_eats', 'v_stg_restaurants') }}
  WHERE cnpj IS NOT NULL
),

prepared AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key(['cnpj']) }} AS hash_hub_cnpj,

    restaurant_id,
    name,
    address,
    city,
    phone_number,
    country,
    cuisine_type,
    opening_time,
    closing_time,
    average_rating,
    num_reviews,

    SHA2(
      CONCAT_WS('|',
        COALESCE(TRIM(restaurant_id), ''),
        COALESCE(TRIM(name), ''),
        COALESCE(TRIM(address), ''),
        COALESCE(TRIM(city), ''),
        COALESCE(TRIM(phone_number), ''),
        COALESCE(TRIM(country), ''),
        COALESCE(TRIM(cuisine_type), ''),
        COALESCE(TRIM(opening_time), ''),
        COALESCE(TRIM(closing_time), ''),
        COALESCE(TO_VARCHAR(average_rating), ''),
        COALESCE(TO_VARCHAR(num_reviews), '')
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
  WHERE (hash_hub_cnpj, hash_diff) NOT IN (
    SELECT hash_hub_cnpj, hash_diff
    FROM {{ this }}
  )
  {% endif %}
)

SELECT *
FROM deduplicated
