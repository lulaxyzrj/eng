{{- config(
    materialized='incremental',
    tags=['raw_vault', 'satellite']
) -}}

{%- set source_model = "stg_status" -%}
{%- set src_pk = "ORDER_HK" -%}
{%- set src_hashdiff = "STATUS_HASHDIFF" -%}
{%- set src_payload = ["STATUS_NAME", "STATUS_TIMESTAMP", "STATUS_ID"] -%}
{%- set src_eff = "EFFECTIVE_FROM" -%}
{%- set src_ldts = "LOAD_DTS" -%}
{%- set src_source = "RECORD_SOURCE" -%}

{{ automate_dv.sat(src_pk=src_pk,
                   src_hashdiff=src_hashdiff,
                   src_payload=src_payload,
                   src_eff=src_eff,
                   src_ldts=src_ldts,
                   src_source=src_source,
                   source_model=source_model) }}