{{- config(
    materialized='view',
    tags=['staging']
) -}}

{%- set yaml_metadata -%}
source_model:
  raw_data: 'RAW_DRIVERS'
derived_columns:
  DRIVER_HK: 'LICENSE_NUMBER'
  DRIVER_HASHDIFF:
    - 'FIRST_NAME'
    - 'LAST_NAME'
    - 'PHONE_NUMBER'
    - 'VEHICLE_TYPE'
    - 'VEHICLE_MAKE'
    - 'VEHICLE_MODEL'
    - 'VEHICLE_YEAR'
  RECORD_SOURCE: '!POSTGRES.DRIVERS'
  EFFECTIVE_FROM: 'LOAD_DTS'
hashed_columns:
  DRIVER_HK: 'LICENSE_NUMBER'
  DRIVER_HASHDIFF:
    - 'FIRST_NAME'
    - 'LAST_NAME'
    - 'PHONE_NUMBER'
    - 'VEHICLE_TYPE'
    - 'VEHICLE_MAKE'
    - 'VEHICLE_MODEL'
    - 'VEHICLE_YEAR'
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns'],
                     ranked_columns=none) }}