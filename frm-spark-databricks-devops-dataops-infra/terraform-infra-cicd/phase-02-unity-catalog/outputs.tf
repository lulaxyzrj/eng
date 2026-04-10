# ==============================================================================
# Phase 02 Outputs
# ==============================================================================

output "metastore_id" {
  description = "Unity Catalog Metastore ID (From Phase 01)"
  value       = local.metastore_id
}

output "storage_credential_name" {
  description = "Storage credential name"
  value       = databricks_storage_credential.unity.name
}

output "external_locations" {
  description = "External locations created"
  value = {
    dev_landing  = databricks_external_location.dev_landing.url
    dev_bronze   = databricks_external_location.dev_bronze.url
    dev_silver   = databricks_external_location.dev_silver.url
    dev_gold     = databricks_external_location.dev_gold.url
    prod_landing = databricks_external_location.prod_landing.url
    prod_bronze  = databricks_external_location.prod_bronze.url
    prod_silver  = databricks_external_location.prod_silver.url
    prod_gold    = databricks_external_location.prod_gold.url
  }
}

output "catalogs" {
  description = "Catalogs created"
  value = {
    dev  = databricks_catalog.dev.name
    prod = databricks_catalog.prod.name
  }
}

output "schemas" {
  description = "Schemas created (fully qualified names)"
  value = {
    dev_bronze  = "${databricks_catalog.dev.name}.${databricks_schema.dev_bronze.name}"
    dev_silver  = "${databricks_catalog.dev.name}.${databricks_schema.dev_silver.name}"
    dev_gold    = "${databricks_catalog.dev.name}.${databricks_schema.dev_gold.name}"
    prod_bronze = "${databricks_catalog.prod.name}.${databricks_schema.prod_bronze.name}"
    prod_silver = "${databricks_catalog.prod.name}.${databricks_schema.prod_silver.name}"
    prod_gold   = "${databricks_catalog.prod.name}.${databricks_schema.prod_gold.name}"
  }
}

# ==============================================================================
# Security Outputs
# ==============================================================================

output "data_engineers_group_id" {
  description = "ID of the data-engineers group"
  value       = databricks_group.data_engineers.id
}

output "data_engineers_members" {
  description = "Members of data-engineers group"
  value       = var.data_engineers_members
}

# ==============================================================================
# Summary
# ==============================================================================

output "summary" {
  description = "Deployment summary"
  value       = <<-EOT

    Unity Catalog Configuration Complete!
    =====================================

    Metastore ID:   ${local.metastore_id}
    Region:         ${local.location}

    Catalogs:
      - ${databricks_catalog.dev.name} (dev - full access for data-engineers)
      - ${databricks_catalog.prod.name} (prod - read-only for data-engineers)

    Schemas (per catalog):
      - bronze (raw data)
      - silver (cleansed)
      - gold (curated)

    External Locations: 8 (landing/bronze/silver/gold x dev/prod)

    Security:
      - Group: data-engineers
      - Members: ${length(var.data_engineers_members)} user(s)

    Dev Workspace:  ${var.dev_workspace_url}
    Prod Workspace: ${var.prod_workspace_url}

  EOT
}