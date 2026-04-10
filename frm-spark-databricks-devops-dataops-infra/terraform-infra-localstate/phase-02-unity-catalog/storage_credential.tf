# ==============================================================================
# Storage Credential
# ==============================================================================
# References the Access Connector. Used by External Locations.
# ==============================================================================

resource "databricks_storage_credential" "unity" {
  provider = databricks.dev

  name    = "${var.prefix}-storage-credential"
  comment = "Storage credential for Unity Catalog (managed by Terraform)"

  azure_managed_identity {
    access_connector_id = local.access_connector_id
  }

  depends_on = [databricks_metastore_assignment.dev]
}