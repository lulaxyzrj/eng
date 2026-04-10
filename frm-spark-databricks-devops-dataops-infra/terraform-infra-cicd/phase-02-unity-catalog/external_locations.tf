# ==============================================================================
# External Locations
# ==============================================================================
# Define paths that Unity Catalog can access.
# 8 locations: landing/bronze/silver/gold x dev/prod
# ==============================================================================

# ------------------------------------------------------------------------------
# Dev Storage
# ------------------------------------------------------------------------------

resource "databricks_external_location" "dev_landing" {
  provider = databricks.dev

  name            = "${var.prefix}-dev-landing"
  url             = "abfss://landing@${local.dev_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.unity.name
  comment         = "Dev environment - Landing layer (raw ingestion)"

  depends_on = [databricks_storage_credential.unity]
}

resource "databricks_external_location" "dev_bronze" {
  provider = databricks.dev

  name            = "${var.prefix}-dev-bronze"
  url             = "abfss://bronze@${local.dev_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.unity.name
  comment         = "Dev environment - Bronze layer"

  depends_on = [databricks_storage_credential.unity]
}

resource "databricks_external_location" "dev_silver" {
  provider = databricks.dev

  name            = "${var.prefix}-dev-silver"
  url             = "abfss://silver@${local.dev_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.unity.name
  comment         = "Dev environment - Silver layer"

  depends_on = [databricks_storage_credential.unity]
}

resource "databricks_external_location" "dev_gold" {
  provider = databricks.dev

  name            = "${var.prefix}-dev-gold"
  url             = "abfss://gold@${local.dev_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.unity.name
  comment         = "Dev environment - Gold layer"

  depends_on = [databricks_storage_credential.unity]
}

# ------------------------------------------------------------------------------
# Prod Storage
# ------------------------------------------------------------------------------

resource "databricks_external_location" "prod_landing" {
  provider = databricks.dev

  name            = "${var.prefix}-prod-landing"
  url             = "abfss://landing@${local.prod_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.unity.name
  comment         = "Prod environment - Landing layer (raw ingestion)"

  depends_on = [databricks_storage_credential.unity]
}

resource "databricks_external_location" "prod_bronze" {
  provider = databricks.dev

  name            = "${var.prefix}-prod-bronze"
  url             = "abfss://bronze@${local.prod_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.unity.name
  comment         = "Prod environment - Bronze layer"

  depends_on = [databricks_storage_credential.unity]
}

resource "databricks_external_location" "prod_silver" {
  provider = databricks.dev

  name            = "${var.prefix}-prod-silver"
  url             = "abfss://silver@${local.prod_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.unity.name
  comment         = "Prod environment - Silver layer"

  depends_on = [databricks_storage_credential.unity]
}

resource "databricks_external_location" "prod_gold" {
  provider = databricks.dev

  name            = "${var.prefix}-prod-gold"
  url             = "abfss://gold@${local.prod_storage_account}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.unity.name
  comment         = "Prod environment - Gold layer"

  depends_on = [databricks_storage_credential.unity]
}
