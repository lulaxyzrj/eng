# Business Vault Layer - AutomateDV

## Overview
The Business Vault extends Raw Vault with business logic, calculations, and query optimization structures. AutomateDV provides specialized structures for performance optimization.

## AutomateDV Business Vault Objects

### 1. **Point-In-Time (PIT) Tables**
Optimize queries across multiple satellites by pre-joining them at specific points in time:

```sql
{{ automate_dv.pit(source_model=source_model,        # Parent hub
                   src_pk=src_pk,                    # Hub primary key
                   as_of_dates_table=as_of_dates_table,
                   satellites=satellites,            # Satellite metadata
                   stage_tables_ldts=stage_tables_ldts,
                   src_ldts=src_ldts) }}
```

**Key Benefits:**
- Eliminates complex joins in queries
- Provides "time travel" capability
- Improves query performance dramatically
- Handles different satellite load frequencies

**Structure Example:**
```yaml
satellites: 
  sat_order_details:
    pk:
      PK: ORDER_HK
    ldts:
      LDTS: LOAD_DTS
```

### 2. **Bridge Tables**
Span relationships across time, connecting hubs through their links:

```sql
{{ automate_dv.bridge(source_model=source_model,
                      src_pk=src_pk,
                      src_ldts=src_ldts,
                      bridge_walk=bridge_walk,
                      as_of_dates_table=as_of_dates_table,
                      stage_tables_ldts=stage_tables_ldts) }}
```

**Key Requirements:**
- Requires Effectivity Satellites
- Uses As-of-Date table for timeline
- Handles relationship validity periods

**Bridge Walk Configuration:**
```yaml
bridge_walk:
  ORDER_DRIVER:
    bridge_link_pk: LINK_ORDER_DRIVER_PK
    link_table: link_order_driver
    eff_sat_table: eff_sat_order_driver
```

### 3. **As-of-Date Tables**
Foundation for PIT and Bridge tables:

```sql
{{ dbt_utils.date_spine(datepart=datepart, 
                        start_date=start_date,
                        end_date=end_date) }}
```

**Key Points:**
- Defines the timeline for analysis
- Usually daily granularity
- Refreshed periodically

## Additional Business Vault Objects (Manual)

### 4. **Business Satellites**
Store calculated metrics and business rules:
- Derived calculations
- Business classifications
- Aggregated metrics
- KPIs and measures

### 5. **Reference Tables (XREF)**
Cross-reference mappings:
```sql
{{ automate_dv.xref(src_pk=src_pk,
                    src_nk=src_nk,
                    src_ldts=src_ldts,
                    src_source=src_source,
                    source_model=source_model) }}
```

## Best Practices
1. **Materialization**: Use `incremental` for PIT/Bridge tables
2. **Performance**: Pre-calculate expensive operations
3. **Business Logic**: Apply rules consistently
4. **Documentation**: Document all business calculations
5. **Testing**: Validate business rules thoroughly