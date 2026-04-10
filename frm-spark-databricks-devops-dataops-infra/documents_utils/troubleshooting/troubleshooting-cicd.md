# CI/CD Troubleshooting Guide

This guide covers common issues encountered when deploying infrastructure via GitHub Actions (CI/CD), specifically focusing on Terraform state management in a remote backend.

## 1. State Inconsistencies (Ghost Resources)

**Symptom:**
*   Pipeline fails with "Resource already exists" errors even though you thought you destroyed everything.
*   `terraform destroy` claims success, but subsequent `apply` fails.
*   The remote state file (`tfstate` in Azure Storage) thinks resources exist, but they don't (or vice versa).

**Cause:**
In a distributed system, network timeouts or API glitches during a `destroy` operation can sometimes leave the Terraform state file (`.tfstate`) out of sync with the actual Azure resources. This is known as "State Drift" or "Ghost Resources".

## 2. The Debug Pipeline: `debug-phase02-state.yaml`

To help diagnose and fix these issues without needing direct access to the production storage account, we have created a specialized **Debug Workflow**.

### Workflow: `Debug Phase 02 State`

**Location:** `.github/workflows/debug-phase02-state.yaml`

**Purpose:**
This pipeline allows you to inspect and manipulate the remote Terraform state for Phase 02 (Unity Catalog) directly from GitHub Actions.

**Capabilities:**
1.  **List State:** Runs `terraform state list` to show exactly what Terraform *thinks* exists.
2.  **Show Resource:** Runs `terraform state show <address>` to reveal details of a specific resource.
3.  **Force Unlock:** If the state is locked by a crashed process, this can clear the lock.
4.  **Remove Resource:** Runs `terraform state rm <address>` to force Terraform to "forget" a resource (useful for ghost resources).

### How to Use It

1.  Go to **GitHub Actions** tab.
2.  Select **"Debug Phase 02 State"** from the left sidebar.
3.  Click **Run workflow**.
4.  **Inputs:**
    *   `command`: Choose the operation (e.g., `list`, `show`, `rm`).
    *   `resource_address`: (Required for `show` or `rm`) The Terraform address of the resource (e.g., `databricks_catalog.dev`).

> **⚠️ Warning:** Using `state rm` is a dangerous operation. It does not delete the real resource, only the record of it. Use this only when you are sure the resource is already deleted or you intend to import it later.

## 3. Common Scenarios

### Scenario A: "Metastore already exists"
*   **Error:** `Error: cannot create metastore: ... already exists`
*   **Fix:**
    1.  Run Debug Pipeline with `command: list`.
    2.  Check if `databricks_metastore.this` is in the list.
    3.  If it IS in the list: The state is correct, but maybe the ID is wrong.
    4.  If it is NOT in the list: The resource exists in Databricks but not in State. You need to `import` it (or delete it manually in Databricks Account Console).

### Scenario B: "Cannot delete schema... not empty"
*   **Context:** During `destroy`.
*   **Fix:** This is usually expected (as noted in the README). If it blocks the pipeline, you can use the Debug Pipeline to `state rm` the schema resource, effectively telling Terraform to ignore it, and then let the subsequent workspace destruction handle the cleanup.
