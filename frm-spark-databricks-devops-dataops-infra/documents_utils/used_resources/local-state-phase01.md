# Terraform Resources Explained: Phase 01 (Azure Infrastructure)

This document details every Terraform resource used in **Phase 01**, explaining its purpose in the UberEats Data Platform architecture.

## 📂 Folder Structure & Resource Mapping

Here is where you can find the resources in the `terraform-infra-localstate/phase-01-azure-infra` directory:

| File Name | Contains Resources For... |
| :--- | :--- |
| **`rg-governance.tf`** | The "Central Governance" layer (Unity Metastore Storage, Access Connector). |
| **`rg-dev.tf`** | The **Development** environment (Workspace, VNet, Storage). |
| **`rg-prod.tf`** | The **Production** environment (Workspace, VNet, Storage). |
| **`providers.tf`** | Azure Provider configuration. |
| **`variables.tf`** | Input variables (Region, Prefix, SKUs). |
| **`outputs.tf`** | Values exported for Phase 02 to use. |

---

## 1. Governance Resources (`rg-governance.tf`)

This file establishes the central governance layer, primarily for Unity Catalog's backend storage.

| Resource Type | Resource Name | Purpose |
| :--- | :--- | :--- |
| `azurerm_resource_group` | `governance` | A dedicated Resource Group (e.g., `ubereats-governance-rg`) to isolate governance assets from Dev/Prod workloads. |
| `azurerm_storage_account` | `unity_metastore` | **ADLS Gen2 Account.** Stores the actual metadata and managed tables for the Unity Catalog Metastore. It is the "brain" of our data governance. |
| `azurerm_storage_container` | `metastore` | The specific container inside the storage account where the metastore data lives. |
| `azurerm_databricks_access_connector` | `unity` | **Critical Security Component.** A Managed Identity wrapper. It allows Databricks to access the ADLS Gen2 storage without needing access keys or service principals. |
| `azurerm_role_assignment` | `unity_metastore` | Grants the Access Connector the `Storage Blob Data Contributor` role on the Metastore Storage Account. This is the permission that actually allows read/write access. |

---

## 2. Development Environment (`rg-dev.tf`)

This file creates the infrastructure for the Development workspace.

| Resource Type | Resource Name | Purpose |
| :--- | :--- | :--- |
| `azurerm_resource_group` | `dev` | Resource Group for all Dev assets (e.g., `ubereats-dev-rg`). |
| `azurerm_virtual_network` | `dev` | **VNet Injection.** A custom Virtual Network for the Databricks workspace. Allows us to control network security (NSGs) and potentially connect to on-premise resources. |
| `azurerm_subnet` | `dev_public` | **Host Subnet.** Used by Databricks for internal cluster communication. (Note: "Public" refers to the subnet type, not necessarily internet exposure). |
| `azurerm_subnet` | `dev_private` | **Container Subnet.** Used by Databricks for the actual compute instances. |
| `azurerm_network_security_group` | `dev` | **Firewall Rules.** Defines inbound/outbound traffic rules for the subnets. We use a `delegation` block to let Databricks manage the necessary rules automatically. |
| `azurerm_subnet_network_security_group_association` | `dev_public/private` | Binds the NSG to the subnets. |
| `azurerm_databricks_workspace` | `dev` | **The Compute Plane.** The actual Databricks environment where users log in and run notebooks. Configured with `no_public_ip = true` for **Secure Cluster Connectivity** (SCC). |
| `azurerm_storage_account` | `dev` | **Data Lake.** The ADLS Gen2 account storing the actual business data (Bronze, Silver, Gold) for the Dev environment. |
| `azurerm_storage_container` | `landing/bronze/silver/gold` | The logical layers of our Medallion Architecture. |
| `azurerm_role_assignment` | `unity_dev` | Grants the **Governance Access Connector** permission to read/write to this Dev Storage Account. This "links" the storage to Unity Catalog. |

---

## 3. Production Environment (`rg-prod.tf`)

This file creates the infrastructure for the Production workspace. It is structurally identical to `rg-dev.tf` but isolated in its own Resource Group.

| Resource Type | Resource Name | Purpose |
| :--- | :--- | :--- |
| `azurerm_resource_group` | `prod` | Resource Group for Prod assets (e.g., `ubereats-prod-rg`). |
| `azurerm_virtual_network` | `prod` | Isolated VNet for Production. |
| `azurerm_subnet` | `prod_public/private` | Subnets for Prod clusters. |
| `azurerm_network_security_group` | `prod` | NSG for Prod. |
| `azurerm_databricks_workspace` | `prod` | The Production Databricks environment. |
| `azurerm_storage_account` | `prod` | **Production Data Lake.** Stores the "real" business data. |
| `azurerm_storage_container` | `landing/bronze/silver/gold` | Medallion layers for Prod. |
| `azurerm_role_assignment` | `unity_prod` | Grants the **Governance Access Connector** permission to this Prod Storage Account. |

---

## 4. Supporting Files

*   **`providers.tf`**: Configures the Azure Provider (`azurerm`) and Terraform version.
*   **`variables.tf`**: Defines input parameters like `prefix` (ubereats), `location` (eastus2), and `databricks_sku` (premium).
*   **`locals.tf`**: Calculates derived values (like subnet CIDR blocks) to keep the main code clean.
*   **`outputs.tf`**: Exports critical IDs (Workspace IDs, Storage Account Names, Access Connector ID) so they can be consumed by **Phase 02**.
