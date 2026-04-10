# ==============================================================================
# Resource Group: Production
# ==============================================================================
# Contains:
# - Databricks Workspace
# - VNet, Subnets, NSG (required for VNet injection)
# - ADLS Gen2 with medallion containers
# ==============================================================================

resource "azurerm_resource_group" "prod" {
  name     = "${local.prod_name}-rg"
  location = var.location
  tags     = local.prod_tags
}

# ==============================================================================
# Networking (required for Databricks VNet injection)
# ==============================================================================

resource "azurerm_virtual_network" "prod" {
  name                = "${local.prod_name}-vnet"
  location            = azurerm_resource_group.prod.location
  resource_group_name = azurerm_resource_group.prod.name
  address_space       = ["10.2.0.0/16"] # Different from dev (10.1.0.0/16)
  tags                = local.prod_tags
}

resource "azurerm_network_security_group" "prod" {
  name                = "${local.prod_name}-nsg"
  location            = azurerm_resource_group.prod.location
  resource_group_name = azurerm_resource_group.prod.name
  tags                = local.prod_tags
}

resource "azurerm_subnet" "prod_public" {
  name                 = "${local.prod_name}-public-subnet"
  resource_group_name  = azurerm_resource_group.prod.name
  virtual_network_name = azurerm_virtual_network.prod.name
  address_prefixes     = ["10.2.1.0/24"]

  delegation {
    name = "databricks-delegation"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
        "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action"
      ]
    }
  }
}

resource "azurerm_subnet" "prod_private" {
  name                 = "${local.prod_name}-private-subnet"
  resource_group_name  = azurerm_resource_group.prod.name
  virtual_network_name = azurerm_virtual_network.prod.name
  address_prefixes     = ["10.2.2.0/24"]

  delegation {
    name = "databricks-delegation"
    service_delegation {
      name = "Microsoft.Databricks/workspaces"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action",
        "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action"
      ]
    }
  }
}

resource "azurerm_subnet_network_security_group_association" "prod_public" {
  subnet_id                 = azurerm_subnet.prod_public.id
  network_security_group_id = azurerm_network_security_group.prod.id
}

resource "azurerm_subnet_network_security_group_association" "prod_private" {
  subnet_id                 = azurerm_subnet.prod_private.id
  network_security_group_id = azurerm_network_security_group.prod.id
}

# ==============================================================================
# Databricks Workspace
# ==============================================================================

resource "azurerm_databricks_workspace" "prod" {
  name                        = "${local.prod_name}-workspace"
  resource_group_name         = azurerm_resource_group.prod.name
  location                    = azurerm_resource_group.prod.location
  sku                         = var.databricks_sku
  managed_resource_group_name = "${local.prod_name}-databricks-managed-rg"
  tags                        = local.prod_tags

  custom_parameters {
    no_public_ip                                         = true
    virtual_network_id                                   = azurerm_virtual_network.prod.id
    public_subnet_name                                   = azurerm_subnet.prod_public.name
    private_subnet_name                                  = azurerm_subnet.prod_private.name
    public_subnet_network_security_group_association_id  = azurerm_subnet_network_security_group_association.prod_public.id
    private_subnet_network_security_group_association_id = azurerm_subnet_network_security_group_association.prod_private.id
  }

  # SAFETY LOCK:
  # Wait for the Account-Level Metastore to be created first.
  # This prevents Databricks from automatically provisioning a system-managed
  # metastore, which would cause "Metastore already exists" conflicts later. +
  # Prevent concurrent workspace creation - Azure API limitation
  depends_on = [
    databricks_metastore.this,
    databricks_metastore_data_access.this,
    azurerm_databricks_workspace.dev
  ]
}

# ==============================================================================
# ADLS Gen2 Storage (Data Lake)
# ==============================================================================

resource "azurerm_storage_account" "prod" {
  name                     = "adls${var.prefix}prod${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.prod.name
  location                 = azurerm_resource_group.prod.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
  tags                     = local.prod_tags
}

# Medallion architecture containers
resource "azurerm_storage_container" "prod" {
  for_each              = toset(local.medallion_containers)
  name                  = each.value
  storage_account_name  = azurerm_storage_account.prod.name
  container_access_type = "private"
}

# ==============================================================================
# Role Assignment: Access Connector -> Prod Storage
# ==============================================================================

resource "azurerm_role_assignment" "unity_prod" {
  scope                = azurerm_storage_account.prod.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.unity.identity[0].principal_id
}
