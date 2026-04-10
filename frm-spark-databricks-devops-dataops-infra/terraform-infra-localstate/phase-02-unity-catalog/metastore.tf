# ==============================================================================
# Metastore Configuration
# ==============================================================================
# One metastore per region. All workspaces in the region share this metastore.
# ==============================================================================

resource "databricks_metastore" "this" {
  provider = databricks.account

  name          = var.metastore_name
  region        = local.location
  storage_root  = local.metastore_storage_path
  force_destroy = true

  lifecycle {
    prevent_destroy = false
  }
}

# ==============================================================================
# Metastore Data Access (link Access Connector to Metastore)
# ==============================================================================

resource "databricks_metastore_data_access" "this" {
  provider = databricks.account

  metastore_id = databricks_metastore.this.id
  name         = "${var.prefix}-access-connector"
  is_default   = true

  azure_managed_identity {
    access_connector_id = local.access_connector_id
  }
}

# ==============================================================================
# Metastore Assignment (link Metastore to Workspaces)
# ==============================================================================

resource "databricks_metastore_assignment" "dev" {
  provider = databricks.account

  metastore_id = databricks_metastore.this.id
  workspace_id = local.dev_workspace_id

  depends_on = [databricks_metastore_data_access.this]
}

resource "databricks_metastore_assignment" "prod" {
  provider = databricks.account

  metastore_id = databricks_metastore.this.id
  workspace_id = local.prod_workspace_id

  depends_on = [databricks_metastore_data_access.this]
}