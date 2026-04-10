### install dbt & snowflake
```sh
pip install dbt
pip install dbt-snowflake

dbt --version
```

### init & check dbt
```sh
DBT_PROFILES_DIR=. dbt debug
DBT_PROFILES_DIR=. dbt deps
```

### run hubs, links & satellites
```sh
DBT_PROFILES_DIR=. dbt run --select raw_vault.hubs
DBT_PROFILES_DIR=. dbt run --select link_order_user_restaurant_driver
DBT_PROFILES_DIR=. dbt run --select raw_vault.satellites

DBT_PROFILES_DIR=. dbt run
```

### get docs
```sh
DBT_PROFILES_DIR=. dbt docs generate
DBT_PROFILES_DIR=. dbt docs serve
```
