# Terraform Resources Explained: CI/CD Phase 01 (Azure Infra)

This document details the resources used in the **CI/CD version** of Phase 01.

## 📂 Folder Structure & Resource Mapping

The structure is nearly identical to the local version, with the addition of backend configuration.

| File Name | Contains Resources For... |
| :--- | :--- |
| **`backend.tf`** | **(New)** Azure Remote Backend configuration. |
| **`rg-governance.tf`** | **(Refactored)** Now owns the **Metastore** creation (Global Resource). |
| **`rg-dev.tf`** | Dev environment (same as local). |
| **`rg-prod.tf`** | Prod environment (same as local). |
| **`providers.tf`** | **(Enhanced)** Includes Databricks Account-level provider. |
| **`variables.tf`** | Inputs (plus new backend variables). |

> **Note:** The core Azure resources (Resource Groups, VNets, Storage) are **identical** to the Local State version. Please refer to **[local-state-phase01.md](local-state-phase01.md)** for the detailed breakdown of those resources.

This document focuses only on the **differences** specific to the CI/CD implementation.

---

## 1. Architectural Shift: Metastore Ownership (`rg-governance.tf`)

In the Local State version, the Metastore is often created in Phase 02. In the **Enterprise CI/CD** architecture, we moved this responsibility to Phase 01.

| Change | Why? |
| :--- | :--- |
| **Metastore Created in Phase 01** | The Metastore is a **Global Resource**. If Phase 02 (Configuration) fails and we destroy it, we don't want to destroy the Metastore itself. By moving it to Phase 01 (Infrastructure), it becomes a permanent foundation, decoupling the "Physical Box" (Metastore) from the "Logical Config" (Catalogs/Grants). |
| **Service Principal Owner** | The CI/CD Service Principal creates the Metastore. This avoids the "User owns the object" problem. |
| **Prevents Default Metastore** | By creating the Metastore *before* the Workspaces (and using `depends_on`), we ensure Databricks doesn't try to auto-provision a "default" metastore for the new workspace, which often caused deployment inconsistencies and "Metastore already exists" errors. |

---

## 2. Backend Configuration (`backend.tf`)

This is the most critical difference.

| Resource / Block | Purpose |
| :--- | :--- |
| `backend "azurerm"` | Tells Terraform to store the state file (`phase-01-azure-infra.tfstate`) in the Azure Storage Account created by the Bootstrap phase. |
| **Why?** | CI/CD pipelines are ephemeral (they start fresh every time). They cannot read a local `terraform.tfstate` file on your laptop. They must fetch the state from a central, shared location (Azure Blob Storage). |

---

## 3. Providers (`providers.tf`)

| Configuration | Purpose |
| :--- | :--- |
| `provider "databricks" { alias = "account" }` | We instantiate the Databricks provider at the **Account Level** (not just Workspace Level). This is required because the Metastore is an Account-level object. |

---

## Summary of Differences

| Feature | Local State | CI/CD State |
| :--- | :--- | :--- |
| **Metastore Owner** | Phase 02 (usually) | **Phase 01 (Infrastructure)** |
| **State Storage** | Local file (`terraform.tfstate`) | Azure Blob Storage |
| **Authentication** | `az login` (User) | Service Principal (App Registration) |
| **Backend Config** | None (Default) | `backend "azurerm" {}` |
