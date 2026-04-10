# ==============================================================================
# Metastore Assignment
# ==============================================================================
# The Metastore itself is now created in Phase 01 (Account Level).
# This phase is responsible only for linking (assigning) that Metastore
# to the specific workspaces (Dev and Prod).
# ==============================================================================

resource "databricks_metastore_assignment" "dev" {
  provider = databricks.account

  # Reads the ID from Phase 01 remote state (defined in data-sources.tf)
  metastore_id = local.metastore_id
  workspace_id = local.dev_workspace_id
}

resource "databricks_metastore_assignment" "prod" {
  provider = databricks.account

  # Reads the ID from Phase 01 remote state
  metastore_id = local.metastore_id
  workspace_id = local.prod_workspace_id
}