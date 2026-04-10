# Infrastructure Approaches: Local State vs. CI/CD (Remote State)

This document outlines the fundamental differences between the **Local State** approach (used in `terraform-infra-localstate`) and the **CI/CD Ready** approach (used in `terraform-infra-cicd`).

We have followed best practices from the [Databricks Terraform Examples](https://github.com/databricks/terraform-databricks-examples/tree/main) to design a robust, production-grade architecture.

## 1. The State Management Dilemma

Terraform tracks the state of your infrastructure in a file called `terraform.tfstate`.

### Local State (The "POC" Way)
*   **Where it lives:** On your laptop's hard drive.
*   **Pros:** Extremely simple. No setup required. Fast.
*   **Cons:**
    *   **No Collaboration:** If another engineer runs the code, they don't have your state file, so Terraform tries to recreate everything (causing conflicts).
    *   **Risk of Data Loss:** If you delete the folder, you lose the mapping to your real resources.
    *   **Security:** Sensitive outputs are stored in plain text on your disk.

### CI/CD Remote State (The "Production" Way)
*   **Where it lives:** In a secure Azure Storage Account container (`tfstate`).
*   **Pros:**
    *   **Collaboration:** Multiple developers/pipelines can work on the same infra.
    *   **Locking:** Azure Blob Storage supports state locking. If two people try to apply at once, one waits.
    *   **Durability:** State is backed up and resilient.
*   **Cons:** Requires an initial "Bootstrap" setup to create the storage account for the state itself.

## 2. The "Chicken and Egg" Problem (Bootstrap)

In a CI/CD setup, we want to store our Terraform state in Azure. But... we need Terraform to create that Azure Storage Account!

**Solution: Phase 00 - Bootstrap**
*   This is a special, one-time execution phase.
*   It creates the **Terraform Backend** resources:
    *   Resource Group (e.g., `ubereats-terraform-backend-rg`)
    *   Storage Account
    *   Container (`tfstate`)
*   Once this exists, Phase 01 and Phase 02 can store their state files (`phase1.tfstate`, `phase2.tfstate`) safely in the cloud.

## 3. Authentication & Execution

| Feature | Local State | CI/CD Ready |
| :--- | :--- | :--- |
| **Who runs it?** | You (User Account) | You (initially) or Service Principal (Pipeline) |
| **Auth Method** | `az login` (CLI) | CLI or Client ID/Secret (SPN) |
| **State File** | `local` | `azurerm` backend (Remote) |
| **Complexity** | Low | Medium (Requires Bootstrap) |

## 4. Why this matters for DevOps

In a real DevOps lifecycle, infrastructure is deployed by **GitHub Actions** or **Azure DevOps Pipelines**, not by a human on a laptop.

*   Pipelines are ephemeral (they start fresh every time). They cannot hold a local state file.
*   Therefore, **Remote State is mandatory** for any automated deployment.

By moving to `terraform-infra-cicd`, you are transitioning from a "Sandbox" environment to a "Professional Engineering" setup.

## 5. Code-Level Differences

If you compare the files in `terraform-infra-localstate` vs `terraform-infra-cicd`, you will spot these specific changes:

### A. The Backend Block (`backend.tf`)
*   **Local:** Does not exist. Terraform defaults to creating a `terraform.tfstate` file in the current directory.
*   **CI/CD:** Contains a `backend "azurerm" { ... }` block. This tells Terraform *not* to save locally, but to talk to Azure Storage.

### B. Data Sources (`data-sources.tf`)
In Phase 02, we need to read outputs (like Workspace URLs) from Phase 01.
*   **Local:** Uses `backend = "local"` and looks for a file path: `path = "../phase-01/terraform.tfstate"`.
*   **CI/CD:** Uses `backend = "azurerm"` and looks for the storage account details.

### C. Variables (`variables.tf`)
*   **Local:** Phase 02 only needs Databricks info.
*   **CI/CD:** Phase 02 has extra variables (`backend_resource_group`, `backend_storage_account`) because it needs to know *where* to find Phase 01's remote state.

### D. Phase 00 (Bootstrap)
*   **Local:** Does not exist.
*   **CI/CD:** A dedicated Terraform project just to create the storage account for the other phases.
