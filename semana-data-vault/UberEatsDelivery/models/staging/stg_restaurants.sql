{{- config(
    materialized='view',
    tags=['staging']
) -}}

{%- set yaml_metadata -%}
source_model:
  raw_data: 'RAW_RESTAURANTS'
derived_columns:
  RESTAURANT_HK: 'CNPJ'
  RECORD_SOURCE: '!MYSQL.RESTAURANTS'
  EFFECTIVE_FROM: 'LOAD_DTS'
hashed_columns:
  RESTAURANT_HK: 'CNPJ'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}