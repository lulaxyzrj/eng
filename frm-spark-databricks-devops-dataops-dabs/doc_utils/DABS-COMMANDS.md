# Databricks Asset Bundles (DABs) - CLI Reference Guide

Complete reference for DABs CLI commands, organized by use case.

---

## Quick Reference Table

| Command | Short Flag | Primary Use Case |
|---------|-----------|------------------|
| `databricks bundle init` | | Create new project from template |
| `databricks bundle validate` | `-t {target}` | Check syntax/vars before deploy |
| `databricks bundle deploy` | `-t {target}` | Push code/config to workspace |
| `databricks bundle run` | `-t {target}` | Execute job & tail logs |
| `databricks bundle destroy` | `-t {target}` | Cleanup/Teardown |
| `databricks bundle summary` | `-t {target}` | List deployed resources & URLs |
| `databricks bundle open` | `-t {target}` | Open workspace in browser |

---

## 1. Project Initialization

### `databricks bundle init`

Interactively scaffolds a new project using an official Databricks template.

```bash
databricks bundle init
```

**When to use:** Starting a new project or onboarding a team. Always use this instead of copying old folders - ensures you have the latest `databricks.yml` structure.

**Available templates:**
- Default Python bundle
- DLT pipeline bundle
- ML project bundle

---

## 2. Development Loop & Validation

### `databricks bundle validate`

Verifies that your `databricks.yml` configuration is syntactically correct and that all referenced resources exist locally. Resolves variable substitutions but does **not** touch the remote workspace.

```bash
# Validate for default target
databricks bundle validate

# Validate for specific target (resolves target-specific variables)
databricks bundle validate -t dev

# Output as JSON (useful for debugging variable resolution)
databricks bundle validate -t dev --output json
```

**When to use:** After any YAML change, before deployment. Catches configuration errors immediately.

---

### `databricks bundle schema`

Outputs the JSON schema for bundle configuration.

```bash
databricks bundle schema > schema.json
```

**When to use:** Configure VS Code or IntelliJ for autocomplete and IntelliSense support in YAML files.

---

## 3. Deployment

### `databricks bundle deploy`

Deploys bundle resources (Jobs, Pipelines, ML Experiments) and uploads local files (Notebooks, Wheels) to the workspace.

```bash
# Deploy to development environment
databricks bundle deploy -t dev

# Deploy with variable override
databricks bundle deploy -t dev --var="service_principal_id=xxx"

# Deploy without confirmation (CI/CD pipelines)
databricks bundle deploy -t prod --auto-approve
```

**Key behavior:**
- Uses Terraform-like state tracking internally
- If you delete a resource from YAML and deploy, it **will be deleted** in the workspace
- First deploy creates resources; subsequent deploys update them

---

### `databricks bundle destroy`

Permanently removes **all resources** associated with the bundle from the target workspace.

```bash
databricks bundle destroy -t dev

# Skip confirmation prompt (required for CI/CD)
databricks bundle destroy -t dev --auto-approve
```

**When to use:** 
- Cleaning up after testing/experiments
- Removing ephemeral CI environments
- Cost management in sandbox environments

> ⚠️ **Warning:** This deletes jobs, pipelines, and files. Use with caution.

---

## 4. Execution & Observability

### `databricks bundle run`

Manually triggers a specific job or pipeline and streams output (logs) to your terminal.

```bash
# Run a specific pipeline
databricks bundle run -t dev order_status_pipeline

# Run with variable
databricks bundle run -t dev order_status_pipeline --var="service_principal_id=xxx"
```

**When to use:** Verify logic immediately after deployment without using the UI.

---

### `databricks bundle summary`

Lists resources deployed for a specific target and their URLs.

```bash
databricks bundle summary -t dev
```

**Output includes:**
- Pipeline URLs
- Job URLs
- App URLs
- Workspace paths

---

### `databricks bundle open`

Opens the workspace in your default browser.

```bash
databricks bundle open -t dev
```

---

## 5. Advanced Debugging

### Debug Logging

Run deployment with verbose logging to see HTTP requests and authentication details.

```bash
databricks bundle deploy -t dev --log-level debug
```

**When to use:** Deployment hangs or fails with vague errors like "Internal Server Error".

---

### JSON Output for Variable Inspection

Dump the fully rendered configuration after all variable substitutions.

```bash
databricks bundle validate -t dev --output json
```

**When to use:** Verify that complex variable overrides (like `${bundle.target}`) resolve correctly.

---

### Internal Terraform Inspection (Advanced)

DABs use Terraform internally. Generated TF files are in `.databricks/bundle/{target}/terraform`.

```bash
# Copy for inspection
cp -r .databricks/bundle/dev/terraform ./terraform-debug
```

**When to use:** Debugging "Terraform Error" messages during DAB deployment.

---

## 6. Common Patterns

### Local Development Cycle

```bash
# 1. Validate configuration
databricks bundle validate -t dev

# 2. Deploy changes
databricks bundle deploy -t dev

# 3. Run and verify
databricks bundle run -t dev order_status_pipeline

# 4. Check results
databricks bundle summary -t dev
```

### CI/CD Pipeline Pattern

```bash
# Validate (fails fast on config errors)
databricks bundle validate -t dev-cicd \
  --var="service_principal_id=${{ secrets.ARM_CLIENT_ID }}"

# Deploy
databricks bundle deploy -t dev-cicd \
  --var="service_principal_id=${{ secrets.ARM_CLIENT_ID }}"

# Run pipeline
databricks bundle run -t dev-cicd order_status_pipeline \
  --var="service_principal_id=${{ secrets.ARM_CLIENT_ID }}"

# Cleanup (E2E tests only)
databricks bundle destroy -t dev-cicd \
  --var="service_principal_id=${{ secrets.ARM_CLIENT_ID }}" \
  --auto-approve
```

### Full Cleanup

```bash
# Destroy all resources for a target
databricks bundle destroy -t dev --auto-approve
```

---

## Variable Passing Methods

Variables can be set in three ways (in order of precedence):

| Method | Example | Precedence |
|--------|---------|------------|
| CLI flag | `--var="catalog=test"` | Highest |
| Target override | `targets.dev.variables.catalog` | Medium |
| Variable default | `variables.catalog.default` | Lowest |

```bash
# Override via CLI (highest priority)
databricks bundle deploy -t dev --var="catalog=ubereats_test"
```

---

## Environment Variables for CI/CD

When using Service Principal authentication:

```bash
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"
export ARM_TENANT_ID="your-tenant-id"
export DATABRICKS_HOST="https://adb-xxx.azuredatabricks.net"
```

The CLI automatically picks up these environment variables.
