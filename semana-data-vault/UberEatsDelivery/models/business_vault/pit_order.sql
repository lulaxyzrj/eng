{{ config(materialized='incremental') }}

{%- set yaml_metadata -%}
source_model: hub_order
src_pk: ORDER_HK
as_of_dates_table: as_of_date
satellites:
  sat_order_details:
    pk:
      PK: ORDER_HK
    ldts:
      LDTS: LOAD_DTS
  sat_order_status:
    pk:
      PK: ORDER_HK
    ldts:
      LDTS: LOAD_DTS
stage_tables_ldts:
  stg_orders: LOAD_DTS
  stg_status: LOAD_DTS
src_ldts: LOAD_DTS
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.pit(source_model=metadata_dict['source_model'],
                   src_pk=metadata_dict['src_pk'],
                   as_of_dates_table=metadata_dict['as_of_dates_table'],
                   satellites=metadata_dict['satellites'],
                   stage_tables_ldts=metadata_dict['stage_tables_ldts'],
                   src_ldts=metadata_dict['src_ldts']) }}