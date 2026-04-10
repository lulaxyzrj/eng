"""
Configuration module for UberEats Dashboard.
Detects environment from app name convention: ubereats-dashboard-{target}
"""
import os
from dataclasses import dataclass


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    catalog: str
    gold_schema: str = "gold"
    silver_schema: str = "silver"
    bronze_schema: str = "bronze"


ENV_CONFIGS = {
    "dev": EnvironmentConfig(catalog="ubereats_dev"),
    "prod": EnvironmentConfig(catalog="ubereats_prod"),
}


def get_target() -> str:
    """Extract target from app name: ubereats-dashboard-dev -> 'dev'"""
    app_name = os.getenv("DATABRICKS_APP_NAME", "unknown-dev")
    return app_name.split("-")[-1]


def get_config() -> EnvironmentConfig:
    """Get configuration for current environment."""
    target = get_target()
    return ENV_CONFIGS.get(target, ENV_CONFIGS["dev"])


def get_warehouse_id() -> str:
    """Get SQL Warehouse ID injected via valueFrom."""
    return os.getenv("DATABRICKS_WAREHOUSE_ID", "")


def get_catalog() -> str:
    """Get catalog name for current environment."""
    return get_config().catalog


def get_schema(layer: str = "gold") -> str:
    """Get schema name for a specific layer."""
    config = get_config()
    schemas = {
        "gold": config.gold_schema,
        "silver": config.silver_schema,
        "bronze": config.bronze_schema,
    }
    return schemas.get(layer, config.gold_schema)


def get_full_table_name(table: str, layer: str = "gold") -> str:
    """Get fully qualified table name: catalog.schema.table"""
    return f"{get_catalog()}.{get_schema(layer)}.{table}"