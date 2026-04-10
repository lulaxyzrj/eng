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
DBT_PROFILES_DIR=. dbt run

DBT_PROFILES_DIR=. dbt run --select staging
DBT_PROFILES_DIR=. dbt test --select staging

DBT_PROFILES_DIR=. dbt run --select tag:hub
DBT_PROFILES_DIR=. dbt run --select tag:link
DBT_PROFILES_DIR=. dbt run --select tag:satellite

DBT_PROFILES_DIR=. dbt run --select as_of_date
DBT_PROFILES_DIR=. dbt run --select pit_order
DBT_PROFILES_DIR=. dbt run --select bridge_order

DBT_PROFILES_DIR=. dbt run --select obt_order_delivery
```

### get docs
```sh
DBT_PROFILES_DIR=. dbt docs generate
DBT_PROFILES_DIR=. dbt docs serve
```
