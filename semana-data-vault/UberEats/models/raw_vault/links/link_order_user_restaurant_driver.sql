{{ config(
    materialized = 'incremental',
    unique_key = 'hash_link_order_user_restaurant_driver'
) }}

WITH source AS (
  SELECT
    order_id,
    cpf,
    cnpj,
    license_number,
    load_dts,
    rec_src AS record_source
  FROM {{ source('uber_eats', 'v_stg_orders') }}
  WHERE order_id IS NOT NULL
    AND cpf IS NOT NULL
    AND cnpj IS NOT NULL
    AND license_number IS NOT NULL
),

hashed AS (
  SELECT
    {{ dbt_utils.generate_surrogate_key([
      'order_id',
      'cpf',
      'cnpj',
      'license_number'
    ]) }} AS hash_link_order_user_restaurant_driver,

    {{ dbt_utils.generate_surrogate_key(['order_id']) }} AS hash_hub_order_id,
    {{ dbt_utils.generate_surrogate_key(['cpf']) }} AS hash_hub_cpf,
    {{ dbt_utils.generate_surrogate_key(['cnpj']) }} AS hash_hub_cnpj,
    {{ dbt_utils.generate_surrogate_key(['license_number']) }} AS hash_hub_license_number,

    'tenant-br' AS multi_tenant_id,
    load_dts,
    record_source
  FROM source
)

SELECT *
FROM hashed

{% if is_incremental() %}
WHERE hash_link_order_user_restaurant_driver NOT IN (
  SELECT hash_link_order_user_restaurant_driver FROM {{ this }}
)
{% endif %}
