{{ config(materialized='incremental') }}

{%- set yaml_metadata -%}
source_model: hub_order
src_pk: ORDER_HK
src_ldts: LOAD_DTS
as_of_dates_table: as_of_date
bridge_walk:
  ORDER_DRIVER:
    bridge_link_pk: LINK_ORDER_DRIVER_PK
    bridge_end_date: EFF_SAT_ORDER_DRIVER_ENDDATE
    bridge_load_date: EFF_SAT_ORDER_DRIVER_LOADDATE
    link_table: link_order_driver
    link_pk: ORDER_DRIVER_HK
    link_fk1: ORDER_HK
    link_fk2: DRIVER_HK
    eff_sat_table: eff_sat_order_driver
    eff_sat_pk: ORDER_DRIVER_HK
    eff_sat_end_date: LOAD_END_DTS
    eff_sat_load_date: LOAD_DTS
stage_tables_ldts:
  stg_orders: LOAD_DTS
{%- endset -%}

{% set metadata_dict = fromyaml(yaml_metadata) %}

{{ automate_dv.bridge(source_model=metadata_dict['source_model'],
                      src_pk=metadata_dict['src_pk'],
                      src_ldts=metadata_dict['src_ldts'],
                      bridge_walk=metadata_dict['bridge_walk'],
                      as_of_dates_table=metadata_dict['as_of_dates_table'],
                      stage_tables_ldts=metadata_dict['stage_tables_ldts']) }}