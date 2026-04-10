# ==============================================================================
# Catalogs and Schemas
# ==============================================================================
# One catalog per environment with medallion architecture schemas.
# ==============================================================================

# ------------------------------------------------------------------------------
# Catalogs
# ------------------------------------------------------------------------------

resource "databricks_catalog" "dev" {
  provider = databricks.dev

  name    = "ubereats_dev"
  comment = "Development catalog for UberEats data platform"

  properties = {
    environment = "development"
    owner       = "data_platform_team"
  }

  depends_on = [databricks_metastore_assignment.dev]
}

resource "databricks_catalog" "prod" {
  provider = databricks.dev

  name    = "ubereats_prod"
  comment = "Production catalog for UberEats data platform"

  properties = {
    environment = "production"
    owner       = "data_platform_team"
  }

  depends_on = [databricks_metastore_assignment.dev]
}

# ------------------------------------------------------------------------------
# Schemas - Dev Catalog
# ------------------------------------------------------------------------------

resource "databricks_schema" "dev_bronze" {
  provider = databricks.dev

  catalog_name = databricks_catalog.dev.name
  name         = "bronze"
  comment      = "Raw data layer - data as ingested from sources"

  properties = {
    layer   = "bronze"
    quality = "raw"
  }
}

resource "databricks_schema" "dev_silver" {
  provider = databricks.dev

  catalog_name = databricks_catalog.dev.name
  name         = "silver"
  comment      = "Cleansed data layer - validated and transformed"

  properties = {
    layer   = "silver"
    quality = "cleansed"
  }
}

resource "databricks_schema" "dev_gold" {
  provider = databricks.dev

  catalog_name = databricks_catalog.dev.name
  name         = "gold"
  comment      = "Curated data layer - business-ready aggregations"

  properties = {
    layer   = "gold"
    quality = "curated"
  }
}

# ------------------------------------------------------------------------------
# Schemas - Prod Catalog
# ------------------------------------------------------------------------------

resource "databricks_schema" "prod_bronze" {
  provider = databricks.dev

  catalog_name = databricks_catalog.prod.name
  name         = "bronze"
  comment      = "Raw data layer - data as ingested from sources"

  properties = {
    layer   = "bronze"
    quality = "raw"
  }
}

resource "databricks_schema" "prod_silver" {
  provider = databricks.dev

  catalog_name = databricks_catalog.prod.name
  name         = "silver"
  comment      = "Cleansed data layer - validated and transformed"

  properties = {
    layer   = "silver"
    quality = "cleansed"
  }
}

resource "databricks_schema" "prod_gold" {
  provider = databricks.dev

  catalog_name = databricks_catalog.prod.name
  name         = "gold"
  comment      = "Curated data layer - business-ready aggregations"

  properties = {
    layer   = "gold"
    quality = "curated"
  }
}
