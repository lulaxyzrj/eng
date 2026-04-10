{{- config(
    materialized='incremental',
    tags=['raw_vault', 'satellite']
) -}}

{%- set source_model = "stg_drivers" -%}
{%- set src_pk = "DRIVER_HK" -%}
{%- set src_hashdiff = "DRIVER_HASHDIFF" -%}
{%- set src_payload = ["FIRST_NAME", "LAST_NAME", "DATE_BIRTH", "PHONE_NUMBER",
                       "CITY", "COUNTRY", "VEHICLE_TYPE", "VEHICLE_MAKE",
                       "VEHICLE_MODEL", "VEHICLE_YEAR"] -%}
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