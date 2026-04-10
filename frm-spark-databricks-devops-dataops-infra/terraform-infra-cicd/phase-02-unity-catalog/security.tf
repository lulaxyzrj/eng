# ==============================================================================
# Security - Groups, Users, and Grants
# ==============================================================================
# This file creates:
# 1. Account-level group (data-engineers)
# 2. Account-level users (with force=true to import existing)
# 3. Group membership
# 4. Workspace assignment (so group can access workspaces)
# 5. Catalog grants (dev: full, prod: read-only)
# 6. Entitlements (cluster creation, SQL access, tokens)
# ==============================================================================

# ------------------------------------------------------------------------------
# Account Group
# ------------------------------------------------------------------------------

resource "databricks_group" "data_engineers" {
  provider     = databricks.account
  display_name = "data-engineers"
}

# ------------------------------------------------------------------------------
# Account Users
# ------------------------------------------------------------------------------
# force = true imports existing users instead of failing

resource "databricks_user" "data_engineers" {
  provider = databricks.account

  for_each  = toset(var.data_engineers_members)
  user_name = each.value
  force     = true
}

# ------------------------------------------------------------------------------
# Group Membership
# ------------------------------------------------------------------------------

resource "databricks_group_member" "data_engineers" {
  provider = databricks.account

  for_each  = toset(var.data_engineers_members)
  group_id  = databricks_group.data_engineers.id
  member_id = databricks_user.data_engineers[each.key].id
}

# ------------------------------------------------------------------------------
# Wait for Identity Federation to be ready
# ------------------------------------------------------------------------------

resource "time_sleep" "wait_for_identity_federation" {
  depends_on = [
    databricks_metastore_assignment.dev,
    databricks_metastore_assignment.prod
  ]

  create_duration = "90s"
}

# ------------------------------------------------------------------------------
# Workspace Assignment - Dev
# ------------------------------------------------------------------------------
# Assigns the account-level group to the workspace so users can login

resource "databricks_mws_permission_assignment" "dev_workspace" {
  provider     = databricks.account
  workspace_id = local.dev_workspace_id
  principal_id = databricks_group.data_engineers.id
  permissions  = ["USER"]

  depends_on = [databricks_metastore_assignment.dev]
}

# ------------------------------------------------------------------------------
# Workspace Assignment - Prod
# ------------------------------------------------------------------------------

resource "databricks_mws_permission_assignment" "prod_workspace" {
  provider     = databricks.account
  workspace_id = local.prod_workspace_id
  principal_id = databricks_group.data_engineers.id
  permissions  = ["USER"]

  depends_on = [databricks_metastore_assignment.prod]
}

# ==============================================================================
# Entitlements - Dev (Power User)
# ==============================================================================
# Enables data-engineers group to:
# - Create clusters (required for Jobs, DLT pipelines)
# - Create instance pools (optional, improves cluster startup time)
# - Access workspace and SQL Warehouses
# - Generate Personal Access Tokens (required for CLI, VS Code, external tools)
# ==============================================================================

# ------------------------------------------------------------------------------
# Lookup group in workspace context
# ------------------------------------------------------------------------------
# Account-level groups are federated to workspaces, but we need the workspace
# context to apply entitlements. The time_sleep ensures federation is complete.

data "databricks_group" "dev_data_engineers" {
  provider     = databricks.dev
  display_name = "data-engineers"

  depends_on = [
    databricks_mws_permission_assignment.dev_workspace,
    time_sleep.wait_for_identity_federation
  ]
}

# ------------------------------------------------------------------------------
# Entitlements: Cluster and Instance Pool Creation (Dev)
# ------------------------------------------------------------------------------
# Required for:
# - Running Jobs (jobs create clusters)
# - DLT / Lakeflow pipelines (create clusters internally)
# - Databricks Apps (may create clusters)

resource "databricks_entitlements" "dev_data_engineers" {
  provider = databricks.dev

  group_id                   = data.databricks_group.dev_data_engineers.id
  allow_cluster_create       = true
  allow_instance_pool_create = true
  workspace_access           = true
  databricks_sql_access      = true

  depends_on = [data.databricks_group.dev_data_engineers]
}

# ==============================================================================
# Entitlements - Prod (Read-Only / Restricted)
# ==============================================================================
# Minimal permissions: can query data via SQL Warehouses but cannot create
# clusters or run jobs directly in production.
# ==============================================================================

data "databricks_group" "prod_data_engineers" {
  provider     = databricks.prod
  display_name = "data-engineers"

  depends_on = [
    databricks_mws_permission_assignment.prod_workspace,
    time_sleep.wait_for_identity_federation
  ]
}

resource "databricks_entitlements" "prod_data_engineers" {
  provider = databricks.prod

  group_id                   = data.databricks_group.prod_data_engineers.id
  allow_cluster_create       = false
  allow_instance_pool_create = false
  workspace_access           = true
  databricks_sql_access      = true

  depends_on = [data.databricks_group.prod_data_engineers]
}

# ==============================================================================
# Grants - Dev Catalog (Full Access)
# ==============================================================================

resource "databricks_grants" "dev_catalog" {
  provider = databricks.dev
  catalog  = databricks_catalog.dev.name

  grant {
    principal  = databricks_group.data_engineers.display_name
    privileges = ["ALL_PRIVILEGES"]
  }

  depends_on = [
    databricks_catalog.dev,
    databricks_group.data_engineers,
    databricks_mws_permission_assignment.dev_workspace
  ]
}

# ==============================================================================
# Grants - Prod Catalog (Read-Only)
# ==============================================================================

resource "databricks_grants" "prod_catalog" {
  provider = databricks.dev
  catalog  = databricks_catalog.prod.name

  grant {
    principal  = databricks_group.data_engineers.display_name
    privileges = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
  }

  depends_on = [
    databricks_catalog.prod,
    databricks_group.data_engineers,
    databricks_mws_permission_assignment.dev_workspace
  ]
}

# ==============================================================================
# Grants - External Locations (Dev) - Full Access
# ==============================================================================

resource "databricks_grants" "dev_landing" {
  provider          = databricks.dev
  external_location = databricks_external_location.dev_landing.id

  grant {
    principal  = databricks_group.data_engineers.display_name
    privileges = ["READ_FILES", "WRITE_FILES"]
  }

  depends_on = [databricks_mws_permission_assignment.dev_workspace]
}

resource "databricks_grants" "dev_bronze" {
  provider          = databricks.dev
  external_location = databricks_external_location.dev_bronze.id

  grant {
    principal  = databricks_group.data_engineers.display_name
    privileges = ["READ_FILES", "WRITE_FILES"]
  }

  depends_on = [databricks_mws_permission_assignment.dev_workspace]
}

resource "databricks_grants" "dev_silver" {
  provider          = databricks.dev
  external_location = databricks_external_location.dev_silver.id

  grant {
    principal  = databricks_group.data_engineers.display_name
    privileges = ["READ_FILES", "WRITE_FILES"]
  }

  depends_on = [databricks_mws_permission_assignment.dev_workspace]
}

resource "databricks_grants" "dev_gold" {
  provider          = databricks.dev
  external_location = databricks_external_location.dev_gold.id

  grant {
    principal  = databricks_group.data_engineers.display_name
    privileges = ["READ_FILES", "WRITE_FILES"]
  }

  depends_on = [databricks_mws_permission_assignment.dev_workspace]
}