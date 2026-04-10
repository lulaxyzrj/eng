# Terraform Resources Explained: CI/CD Phase 02 (Unity Catalog)

This document details the resources used in the **CI/CD version** of Phase 02.

## 📂 Folder Structure & Resource Mapping

The structure mirrors the local version, but with key differences in how state is read and security is managed.

| File Name | Contains Resources For... |
| :--- | :--- |
| **`backend.tf`** | **(New)** Azure Remote Backend configuration. |
| **`data-sources.tf`** | **(Modified)** Reads Phase 01 state. Uses `try()` logic for CI robustness. |
| **`security.tf`** | **(Enhanced)** Automated Entitlements and Token permissions. |
| **`metastore.tf`** | **(Refactored)** Now only **binds** the Metastore (Assignment), does NOT create it. |
| **`catalogs.tf`** | Catalog resources (same as local). |

> **Note:** The core Unity Catalog resources (Metastore, Catalogs, External Locations) are **identical** to the Local State version. Please refer to **[local-state-phase02.md](local-state-phase02.md)** for the detailed breakdown of those resources.

This document focuses on the **differences** specific to the CI/CD implementation, particularly in **Security** and **State Management**.

---

## 1. Architectural Shift: Metastore Consumption (`metastore.tf`)

In the Local State version, Phase 02 creates the Metastore. In the **Enterprise CI/CD** architecture, Phase 02 only **consumes** it.

| Change | Why? |
| :--- | :--- |
| **No `databricks_metastore` resource** | Phase 02 does NOT create the metastore. It reads the `metastore_id` from Phase 01 outputs. |
| **Focus on Assignment** | Phase 02 is responsible only for `databricks_metastore_assignment` (binding the Metastore to the Workspaces). |

---

## 2. Robust Data Sources (`data-sources.tf`)

We use advanced Terraform functions to make the CI/CD pipeline resilient.

| Technique | Code Example | Purpose |
| :--- | :--- | :--- |
| **`try()` Function** | `metastore_id = try(data.terraform_remote_state.phase_01.outputs.metastore_id, "placeholder")` | **Prevents CI Failures.** When running `terraform plan` for the first time in a PR, Phase 01 might not exist yet. `try()` allows the plan to succeed with a placeholder value instead of crashing. |

---

## 3. Enhanced Security (`security.tf`)

The CI/CD version includes automation for permissions that are often done manually in local setups.

| Resource Type | Resource Name | Purpose (CI/CD Specific) |
| :--- | :--- | :--- |
| `databricks_entitlements` | `dev_data_engineers` | **Power User Rights.** Automatically grants the `data-engineers` group the right to **Create Clusters** and **Access SQL** in the Dev workspace. In local setups, admins often click these checkboxes manually in the UI. |
| `databricks_permissions` | `dev_token_usage` | **Token Management.** Explicitly grants the `data-engineers` group the `CAN_USE` permission on Tokens. This is critical for developers to generate Personal Access Tokens (PATs) for CLI or IDE access. |
| `databricks_entitlements` | `prod_data_engineers` | **Restricted Rights.** Explicitly *denies* cluster creation in Prod (`allow_cluster_create = false`), enforcing the "Code Only" deployment policy for Production. |

---

## Summary of Differences

| Feature | Local State | CI/CD State |
| :--- | :--- | :--- |
| **Metastore Role** | Creator | **Consumer (Assignment Only)** |
| **CI Robustness** | Basic | Uses `try()` to handle missing dependencies during Plan |
| **Entitlements** | Often Manual | Fully Automated (Cluster Create, SQL Access) |
| **Token Access** | Default / Manual | Explicitly Managed via Terraform |
| **Prod Restrictions** | Manual Policy | Enforced via Code (`allow_cluster_create = false`) |
