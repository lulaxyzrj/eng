# UberEats Data Vault Implementation with AutomateDV

## Overview

This project demonstrates a complete Data Vault 2.0 implementation using **AutomateDV** and **dbt** on Snowflake. It models a food delivery platform (UberEats) with end-to-end data pipelines from raw staging through to business-ready information delivery.

## Project Structure

```
UberEatsDelivery/
├── models/
│   ├── staging/               # AutomateDV staging layer with hash keys
│   │   ├── stg_orders.sql
│   │   ├── stg_drivers.sql
│   │   ├── stg_status.sql
│   │   └── README.md
│   ├── raw_vault/            # Core Data Vault structures
│   │   ├── hubs/            # Business entities
│   │   │   ├── hub_order.sql
│   │   │   └── hub_driver.sql
│   │   ├── links/           # Relationships
│   │   │   └── link_order_driver.sql
│   │   ├── satellites/      # Descriptive attributes & history
│   │   │   ├── sat_order_details.sql
│   │   │   ├── sat_order_status.sql
│   │   │   ├── sat_driver_details.sql
│   │   │   └── eff_sat_order_driver.sql
│   │   └── README.md
│   ├── business_vault/       # Performance & business structures
│   │   ├── as_of_date.sql  # Timeline for PIT/Bridge
│   │   ├── pit_order.sql    # Point-in-time table
│   │   ├── bridge_order.sql # Bridge table
│   │   └── README.md
│   └── information_delivery/ # Business-ready data
│       ├── obt_order_delivery.sql
│       └── README.md
├── dbt_project.yml          # dbt configuration
├── profiles.yml             # Connection settings
└── packages.yml             # AutomateDV dependency

```

## Key Features

### 1. **AutomateDV Integration**
- Automated hash key generation
- Built-in Data Vault patterns
- Standardized metadata handling
- CDC and historization support

### 2. **Business Entities Modeled**
- **Orders**: Core transaction entity
- **Drivers**: Delivery personnel
- **Order Status**: Full delivery lifecycle tracking

### 3. **Advanced Data Vault Concepts**
- **Effectivity Satellites**: Track relationship validity
- **PIT Tables**: Optimize time-based queries
- **Bridge Tables**: Span relationships across time
- **Business Vault**: Apply business rules and calculations

## Getting Started

### Prerequisites
- Snowflake account with appropriate permissions
- Python 3.8+ with dbt-core and dbt-snowflake
- Access to stage area with source JSON files

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd UberEatsDelivery
   ```

2. **Install dependencies**
   ```bash
   pip install dbt-core dbt-snowflake
   dbt deps  # Installs AutomateDV
   ```

3. **Configure connection**
   Update `profiles.yml` with your Snowflake credentials:
   ```yaml
   ubereats_datavault:
     outputs:
       dev:
         type: snowflake
         account: <your-account>
         user: <your-user>
         password: <your-password>
         role: ACCOUNTADMIN
         database: UBEREATS
         warehouse: UBEREATS
         schema: public
   ```

### Running the Project

1. **Load raw data to Snowflake tables**
   ```sql
   -- Run the provided SQL script to load from stage
   -- See snowflake_scripts/01_load_stage_to_raw_tables.sql
   ```

2. **Run dbt models in sequence**
   ```bash
   # Test connection
   DBT_PROFILES_DIR=. dbt debug
   
   # Run staging layer
   DBT_PROFILES_DIR=. dbt run --select staging
   
   # Run raw vault
   DBT_PROFILES_DIR=. dbt run --select tag:raw_vault
   
   # Run business vault
   DBT_PROFILES_DIR=. dbt run --select tag:business_vault
   
   # Run information delivery
   DBT_PROFILES_DIR=. dbt run --select tag:information_delivery
   
   # Or run everything
   DBT_PROFILES_DIR=. dbt run
   ```

## AutomateDV Macros Used

### Staging Layer
- `automate_dv.stage()` - Prepares data with hash keys and metadata

### Raw Vault Layer
- `automate_dv.hub()` - Creates hub tables for business entities
- `automate_dv.link()` - Creates link tables for relationships
- `automate_dv.sat()` - Creates satellite tables for attributes
- `automate_dv.eff_sat()` - Creates effectivity satellites (manual implementation)

### Business Vault Layer
- `automate_dv.pit()` - Creates point-in-time tables
- `automate_dv.bridge()` - Creates bridge tables
- `dbt_utils.date_spine()` - Generates as-of-date sequences

## Data Flow Example

1. **Raw Order Data** → Staging adds `ORDER_HK`, `DRIVER_HK`, `ORDER_DRIVER_HK`
2. **Staging** → Hub stores unique orders, Link captures order-driver relationship
3. **Satellites** → Track order details and status changes over time
4. **PIT Table** → Combines latest order details and status at any point in time
5. **OBT** → Denormalized view with all order, driver, and delivery metrics

## Key Concepts Demonstrated

### Data Vault 2.0 Principles
- **Hubs**: Store only business keys (ORDER_ID, LICENSE_NUMBER)
- **Links**: Capture relationships without descriptive data
- **Satellites**: All descriptive attributes with full history
- **Insert-Only**: No updates or deletes, maintaining full audit trail

### AutomateDV Benefits
- **Standardization**: Consistent patterns across all vault objects
- **Automation**: Hash keys and metadata handled automatically
- **Performance**: Built-in optimizations for Snowflake
- **Maintainability**: Declarative YAML-based configurations

## Troubleshooting

### Common Issues
1. **"Object not found"**: Ensure source views/tables exist
2. **"Duplicate column"**: Check for column naming conflicts in satellites
3. **"Invalid identifier"**: Verify column names match between layers

### Performance Tips
- Use `incremental` materialization for large tables
- Create clustered keys on frequently joined columns
- Monitor Snowflake query history for optimization opportunities

## Further Learning

- [AutomateDV Documentation](https://automate-dv.readthedocs.io/)
- [Data Vault 2.0 Standards](https://datavaultalliance.com/)
- [dbt Documentation](https://docs.getdbt.com/)

## Contributing

Feel free to submit issues or pull requests to improve this implementation.

## License

This project is for educational purposes as part of the Data Engineering Academy.