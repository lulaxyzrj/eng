# Terraform Resources Explained: Phase 02 (Unity Catalog)

This document details every Terraform resource used in **Phase 02**, explaining how we configure the logical data governance layer on top of the Azure infrastructure.

## 📂 Folder Structure & Resource Mapping

Here is where you can find the resources in the `terraform-infra-localstate/phase-02-unity-catalog` directory:

| File Name | Contains Resources For... |
| :--- | :--- |
| **`metastore.tf`** | The Unity Catalog Metastore itself and its workspace assignments. |
| **`storage_credential.tf`** | The bridge to Azure Storage (using the Access Connector). |
| **`external_locations.tf`** | Definitions of *where* data lives (Landing, Bronze, Silver, Gold). |
| **`catalogs.tf`** | Logical organization (Dev Catalog, Prod Catalog, Schemas). |
| **`security.tf`** | Users, Groups, and Permissions (Grants). |
| **`data-sources.tf`** | Reading outputs from Phase 01 (to know Storage Account names, etc.). |
| **`providers.tf`** | Databricks Provider configuration (with aliases for Dev/Prod). |

---

## 1. The Metastore (`metastore.tf`)

The Metastore is the top-level container for all data in Unity Catalog.

| Resource Type | Resource Name | Purpose |
| :--- | :--- | :--- |
| `databricks_metastore` | `this` | Creates the actual Unity Catalog Metastore object. It is a regional singleton (one per region per account). |
| `databricks_metastore_data_access` | `this` | Configures the **Root Storage** for the metastore. It tells Databricks: "Use this Access Connector (Managed Identity) to talk to this ADLS Container (created in Phase 01)." |
| `databricks_metastore_assignment` | `dev` / `prod` | **Workspace Binding.** Attaches the Metastore to the Dev and Prod workspaces so they can "see" the data. |

---

## 2. Storage Access (`storage_credential.tf`)

This is the bridge between Databricks and Azure Security.

| Resource Type | Resource Name | Purpose |
| :--- | :--- | :--- |
| `databricks_storage_credential` | `external` | Represents the **Azure Access Connector** inside Databricks. It says: "I have a credential that allows access to Azure Storage." Users don't use this directly; it's used by External Locations. |

---

## 3. External Locations (`external_locations.tf`)

These define *where* data lives and *how* to access it.

| Resource Type | Resource Name | Purpose |
| :--- | :--- | :--- |
| `databricks_external_location` | `dev_landing` | Points to `abfss://landing@dev_storage...`. Uses the Storage Credential. |
| `databricks_external_location` | `dev_bronze` | Points to `abfss://bronze@dev_storage...`. |
| `databricks_external_location` | `...` | (Repeated for Silver/Gold in both Dev and Prod). These allow us to create Managed Tables or External Tables in these specific paths. |

---

## 4. Catalogs & Schemas (`catalogs.tf`)

The logical organization of data.

| Resource Type | Resource Name | Purpose |
| :--- | :--- | :--- |
| `databricks_catalog` | `dev` | Creates the catalog `ubereats_dev`. This isolates Development data. |
| `databricks_catalog` | `prod` | Creates the catalog `ubereats_prod`. This isolates Production data. |
| `databricks_schema` | `dev_bronze` | Creates the schema `ubereats_dev.bronze`. |
| `databricks_schema` | `...` | (Repeated for Silver/Gold). Note: We don't create a "Landing" schema because Landing is usually just raw files, not tables. |

---

## 5. Security & Grants (`security.tf`)

This file implements the **Access Control** model.

| Resource Type | Resource Name | Purpose |
| :--- | :--- | :--- |
| `databricks_group` | `data_engineers` | Creates the `data-engineers` group in the Account Console. |
| `databricks_user` | `data_engineers` | Adds users (from the variable list) to the Account. |
| `databricks_group_member` | `data_engineers` | Adds the users to the group. |
| `databricks_mws_permission_assignment` | `dev_workspace` | **Workspace Access.** Allows the `data-engineers` group to log in to the Dev Workspace. |
| `databricks_grants` | `dev_catalog` | **Full Access.** Grants `ALL_PRIVILEGES` on `ubereats_dev` to `data-engineers`. |
| `databricks_grants` | `prod_catalog` | **Read-Only.** Grants `SELECT` (and usage) on `ubereats_prod` to `data-engineers`. |
| `databricks_grants` | `dev_landing` | **File Access.** Grants `READ_FILES` / `WRITE_FILES` on the External Locations so engineers can upload/read raw files. |

---

## 6. Supporting Files

*   **`providers.tf`**: Configures the Databricks provider. Crucially, it sets up **multiple aliases** (`alias = "dev"`, `alias = "prod"`) so Terraform can manage resources in different workspaces simultaneously.
*   **`data-sources.tf`**: Reads the `terraform_remote_state` from Phase 01 to get the Storage Account names and Access Connector IDs.
*   **`variables.tf`**: Input variables (Account ID, User Emails).
