{{- config(
    materialized='incremental',
    tags=['raw_vault', 'hub']
) -}}

{%- set source_model = ["stg_orders", "stg_status"] -%}
{%- set src_pk = "ORDER_HK" -%}
{%- set src_nk = "ORDER_ID" -%}
{%- set src_ldts = "LOAD_DTS" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.hub(src_pk=src_pk,
                   src_nk=src_nk,
                   src_ldts=src_ldts,
                   src_source=src_source,
                   source_model=source_model) }}