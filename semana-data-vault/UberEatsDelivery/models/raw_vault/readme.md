# Raw Vault Layer - AutomateDV

## Overview
The Raw Vault is the core of Data Vault 2.0, storing business data in its most granular form. AutomateDV provides specialized macros for each Raw Vault object type.

## AutomateDV Raw Vault Objects

### 1. **Hubs** - Business Entities
Store unique business keys using the `hub` macro:
```sql
{{ automate_dv.hub(src_pk=src_pk,      # Hash key
                   src_nk=src_nk,      # Business key
                   src_ldts=src_ldts,  # Load timestamp
                   src_source=src_source,
                   source_model=source_model) }}
```

**Key Points:**
- Hubs only store business keys and metadata
- Can have multiple source models
- Use incremental materialization

### 2. **Links** - Relationships
Capture relationships between business entities:
```sql
{{ automate_dv.link(src_pk=src_pk,     # Link hash key
                    src_fk=src_fk,     # List of hub hash keys
                    src_ldts=src_ldts,
                    src_source=src_source,
                    source_model=source_model) }}
```

**Key Points:**
- Links are many-to-many by design
- Foreign keys must be provided as a list
- Links never contain descriptive attributes

### 3. **Satellites** - Descriptive Attributes
Store descriptive data and track changes over time:
```sql
{{ automate_dv.sat(src_pk=src_pk,           # Parent hub/link key
                   src_hashdiff=src_hashdiff, # Change detection
                   src_payload=src_payload,   # Business attributes
                   src_eff=src_eff,          # Effective date
                   src_ldts=src_ldts,
                   src_source=src_source,
                   source_model=source_model) }}
```

**Key Points:**
- Satellites track full history
- Use hashdiff for change data capture
- Can hang off both Hubs and Links

### 4. **Effectivity Satellites** - Relationship Validity
Track when relationships are valid:
```sql
{{ automate_dv.eff_sat(src_pk=src_pk,
                       src_dfk=src_dfk,     # Driving foreign key
                       src_sfk=src_sfk,     # Secondary foreign key
                       src_start_date=src_start_date,
                       src_end_date=src_end_date,
                       src_eff=src_eff,
                       src_ldts=src_ldts,
                       src_source=src_source,
                       source_model=source_model) }}
```

## Materialization Strategy
- **Hubs & Links**: Use `incremental` for append-only behavior
- **Satellites**: Use `incremental` with proper change detection
- **Initial Load**: Consider `table` for first run, then switch to `incremental`

## Data Vault Rules (Enforced by AutomateDV)
1. Hubs contain only business keys
2. Links only contain relationships (no descriptive data)
3. All descriptive data goes in Satellites
4. All objects are insert-only (no updates/deletes)
5. Track record source and load timestamps