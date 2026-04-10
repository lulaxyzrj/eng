{{ config(
    materialized = 'incremental',
    unique_key = ['hash_hub_license_number', 'load_dts']
) }}

WITH source AS (
  SELECT
    license_number,
    driver_id,
    first_name,
    last_name,
    date_birth,
    phone_number,
    city,
    country,
    vehicle_type,
    vehicle_make,
    vehicle_model,
    vehicle_year,
    load_dts,
    rec_src AS record_source
  FROM {{ source('uber_eats', 'v_stg_drivers') }}
  WHERE license_number IS NOT NULL
),

prepared AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key(['license_number']) }} AS hash_hub_license_number,

    driver_id,
    first_name,
    last_name,
    date_birth,
    phone_number,
    city,
    country,
    vehicle_type,
    vehicle_make,
    vehicle_model,
    vehicle_year,

    SHA2(
      CONCAT_WS('|',
        COALESCE(TRIM(driver_id), ''),
        COALESCE(TRIM(first_name), ''),
        COALESCE(TRIM(last_name), ''),
        COALESCE(TO_VARCHAR(date_birth), ''),
        COALESCE(TRIM(phone_number), ''),
        COALESCE(TRIM(city), ''),
        COALESCE(TRIM(country), ''),
        COALESCE(TRIM(vehicle_type), ''),
        COALESCE(TRIM(vehicle_make), ''),
        COALESCE(TRIM(vehicle_model), ''),
        COALESCE(TO_VARCHAR(vehicle_year), '')
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
  WHERE (hash_hub_license_number, hash_diff) NOT IN (
    SELECT hash_hub_license_number, hash_diff
    FROM {{ this }}
  )
  {% endif %}
)

SELECT *
FROM deduplicated
