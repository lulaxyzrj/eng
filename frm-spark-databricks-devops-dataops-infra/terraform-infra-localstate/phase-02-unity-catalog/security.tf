# ==============================================================================
# Security - Groups, Users, and Grants
# ==============================================================================
# This file creates:
# 1. Account-level group (data-engineers)
# 2. Account-level users (with force=true to import existing)
# 3. Group membership
# 4. Workspace assignment (so group can access workspaces)
# 5. Catalog grants (dev: full, prod: read-only)
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

  create_duration = "60s"
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

# ------------------------------------------------------------------------------
# Grants - Dev Catalog (Full Access)
# ------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------
# Grants - Prod Catalog (Read-Only)
# ------------------------------------------------------------------------------

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


# ------------------------------------------------------------------------------
# Grants - External Locations (Dev)
# ------------------------------------------------------------------------------

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


# ------------------------------------------------------------------------------
# Grants - External Locations (Prod)
# ------------------------------------------------------------------------------
# Prod landing: READ-ONLY (dados chegam de fora, engenheiros só leem)
# Prod bronze/silver/gold: SEM GRANTS (acesso via managed tables apenas)

resource "databricks_grants" "prod_landing" {
  provider          = databricks.dev
  external_location = databricks_external_location.prod_landing.id

  grant {
    principal  = databricks_group.data_engineers.display_name
    privileges = ["READ_FILES"]  # READ-ONLY
  }

  depends_on = [databricks_mws_permission_assignment.dev_workspace]
}
