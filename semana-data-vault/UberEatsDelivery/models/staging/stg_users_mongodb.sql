{{- config(
    materialized='view',
    tags=['staging']
) -}}

{%- set yaml_metadata -%}
source_model:
  raw_data: 'RAW_USERS_MONGODB'
derived_columns:
  USER_HK: 'CPF'
  RECORD_SOURCE: '!MONGODB.USERS'
  EFFECTIVE_FROM: 'LOAD_DTS'
hashed_columns:
  USER_HK: 'CPF'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}