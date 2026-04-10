{{- config(
    materialized='view',
    tags=['staging']
) -}}

{%- set yaml_metadata -%}
source_model:
  raw_data: 'RAW_STATUS'
derived_columns:
  ORDER_HK: 'ORDER_ID'
  RECORD_SOURCE: '!KAFKA.STATUS'
  EFFECTIVE_FROM: 'STATUS_TS_PARSED'
  STATUS_HASHDIFF:
    - 'STATUS_NAME'
    - 'STATUS_TIMESTAMP'
hashed_columns:
  ORDER_HK: 'ORDER_ID'
  STATUS_HASHDIFF:
    - 'STATUS_NAME'
    - 'STATUS_TIMESTAMP'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}