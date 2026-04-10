# Staging Layer - AutomateDV

## Overview
The Staging layer is the foundation of any Data Vault implementation using AutomateDV. It prepares raw data for loading into the Raw Vault by adding required metadata and hash keys.

## Key AutomateDV Features

### 1. **Hash Key Generation**
AutomateDV automatically generates hash keys for business entities and relationships:
```yaml
hashed_columns:
  ORDER_HK: 'ORDER_ID'           # Hub hash key
  DRIVER_HK: 'LICENSE_NUMBER'    # Hub hash key
  ORDER_DRIVER_HK:               # Link hash key
    - 'ORDER_ID'
    - 'LICENSE_NUMBER'
```

### 2. **Metadata Columns**
AutomateDV adds essential Data Vault metadata:
- `RECORD_SOURCE`: Identifies the source system (e.g., '!KAFKA.ORDERS')
- `EFFECTIVE_FROM`: Business effective date
- `LOAD_DTS`: Technical load timestamp

### 3. **The `stage` Macro**
```sql
{{ automate_dv.stage(include_source_columns=true,
                     source_model=metadata_dict['source_model'],
                     derived_columns=metadata_dict['derived_columns'],
                     hashed_columns=metadata_dict['hashed_columns']) }}
```

## Important Considerations

1. **Naming Conventions**: Use consistent naming for hash keys (e.g., `_HK` suffix)
2. **Source Tracking**: Always include meaningful record source identifiers
3. **Hash Diff**: For satellites, create hash diffs to detect changes:
   ```yaml
   HASHDIFF:
     - 'STATUS_NAME'
     - 'STATUS_TIMESTAMP'
   ```

## Best Practices
- Keep staging models as views for real-time data freshness
- Use uppercase for column names (Data Vault convention)
- Include all columns needed for downstream Raw Vault objects
- Test hash key generation to ensure uniqueness