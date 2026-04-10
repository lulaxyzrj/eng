{{- config(
    materialized='view',
    tags=['staging']
) -}}

{%- set yaml_metadata -%}
source_model:
  raw_data: 'RAW_ORDERS'
derived_columns:
  ORDER_HK: 'ORDER_ID'
  DRIVER_HK: 'LICENSE_NUMBER'
  ORDER_DRIVER_HK:
    - 'ORDER_ID'
    - 'LICENSE_NUMBER'
  ORDER_HASHDIFF:
    - 'ORDER_DATE'
    - 'TOTAL_AMOUNT'
    - 'PAYMENT_KEY'
  RECORD_SOURCE: '!KAFKA.ORDERS'
  EFFECTIVE_FROM: 'LOAD_DTS'
  LOAD_END_DTS: '!9999-12-31'
  LOAD_END_DTS: '!9999-12-31 23:59:59.999999'
  LOAD_END_DTS: '!9999-12-31 23:59:59.999999'
hashed_columns:
  ORDER_HK: 'ORDER_ID'
  DRIVER_HK: 'LICENSE_NUMBER'
  ORDER_DRIVER_HK:
    - 'ORDER_ID'
    - 'LICENSE_NUMBER'
  ORDER_HASHDIFF:
    - 'ORDER_DATE'
    - 'TOTAL_AMOUNT'
    - 'PAYMENT_KEY'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}