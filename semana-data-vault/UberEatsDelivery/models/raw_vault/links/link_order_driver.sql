{{- config(
    materialized='incremental',
    tags=['raw_vault', 'link']
) -}}

{%- set source_model = "stg_orders" -%}
{%- set src_pk = "ORDER_DRIVER_HK" -%}
{%- set src_fk = ["ORDER_HK", "DRIVER_HK"] -%}
{%- set src_ldts = "LOAD_DTS" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.link(src_pk=src_pk,
                    src_fk=src_fk,
                    src_ldts=src_ldts,
                    src_source=src_source,
                    source_model=source_model) }}