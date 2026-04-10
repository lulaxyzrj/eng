# Essential Terraform Commands Cheat Sheet

This guide covers the most frequently used Terraform commands in our UberEats Data Platform project. It focuses on commands you will use for both **Local State** development and **CI/CD** debugging.

---

## 1. Core Workflow (Day-to-Day)

These are the commands you run to deploy and manage infrastructure.

### `terraform init`
**Purpose:** Initializes the working directory. It downloads providers (Azure, Databricks) and configures the backend (State).
*   **When to use:** First time you enter a folder, or after changing `providers.tf` / `backend.tf`.
*   **Project Context:**
    *   **Local:** Just run `terraform init`.
    *   **CI/CD:** We use `terraform init -backend-config=...` to dynamically tell Terraform where the Azure Storage Account is.

### `terraform plan`
**Purpose:** Creates an execution plan. It compares your code (`.tf` files) with the current state (`.tfstate`) and real Azure resources.
*   **When to use:** Always run this before `apply` to see what *will* happen.
*   **Key Output:** Look for `+ create`, `~ update`, or `- destroy`.

### `terraform apply`
**Purpose:** Executes the changes proposed in the plan.
*   **When to use:** When you are ready to create/update resources.
*   **Flags:**
    *   `-auto-approve`: Skips the "yes" confirmation prompt (Used in our CI/CD pipelines).

### `terraform destroy`
**Purpose:** Destroys all resources managed by the current configuration.
*   **When to use:** To clean up the POC or save costs.
*   **Warning:** This is destructive! In our project, we have a `99-destroy-all.sh` script that orchestrates this safely.

---

## 2. Outputs & Inspection

Commands to see what Terraform knows about your infrastructure.

### `terraform output`
**Purpose:** Prints the values defined in `outputs.tf`.
*   **When to use:** To get connection strings, workspace URLs, or IDs after a deployment.
*   **Flags:**
    *   `-json`: Returns output in JSON format (Used by our scripts to pass data between phases).
    *   `-raw <name>`: Returns the string value without quotes (Useful for `client_secret`).

### `terraform console`
**Purpose:** Opens an interactive shell to experiment with Terraform expressions.
*   **When to use:** Debugging variables or locals.
*   **Example:** Type `local.location` to see what value it holds.

---

## 3. Code Quality

Keep your code clean and error-free.

### `terraform fmt`
**Purpose:** Rewrites Terraform configuration files to a canonical format and style.
*   **When to use:** Before committing code. It fixes indentation and spacing automatically.
*   **Tip:** Run `terraform fmt -recursive` to format all subdirectories.

### `terraform validate`
**Purpose:** Validates the configuration files for syntax errors and internal consistency.
*   **When to use:** To check for typos or missing required arguments before running `plan`.

---

## 4. Advanced State Management (Troubleshooting)

These commands are critical when Terraform gets "confused" or when you need to fix "State Inconsistencies" (as mentioned in our troubleshooting guides).

### `terraform state list`
**Purpose:** Lists all resources currently tracked in your state file.
*   **When to use:** To verify if a resource (e.g., `azurerm_resource_group.this`) is actually being managed by Terraform.

### `terraform state show <resource_address>`
**Purpose:** Shows detailed attributes of a single resource in the state.
*   **Example:** `terraform state show azurerm_databricks_workspace.dev`

### `terraform state rm <resource_address>`
**Purpose:** Removes a resource from the Terraform state *without* destroying the real object in Azure.
*   **When to use:**
    *   If you manually deleted a resource in Azure and Terraform is stuck trying to find it.
    *   To "forget" a resource so Terraform tries to create it again (use with caution!).

### `terraform import <resource_address> <resource_id>`
**Purpose:** Imports an existing Azure resource into Terraform state.
*   **When to use:**
    *   If you created a resource manually (e.g., the Default Metastore) and want Terraform to manage it.
    *   **Project Context:** Often used to fix "Resource already exists" errors.

---

## 5. CI/CD Specific Flags

You will see these in our GitHub Actions YAML files.

*   `-input=false`: Disables interactive prompts (crucial for automation).
*   `-backend-config="key=value"`: Passes backend configuration (Resource Group, Storage Account) at runtime, keeping our code generic.
