# GitHub Actions Workflows for Databricks Asset Bundles

This document explains the CI/CD pipelines that automate bundle deployment.

---

## Workflow Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WORKFLOW ARCHITECTURE                              │
│                                                                             │
│   MANUAL WORKFLOWS                      AUTOMATED WORKFLOWS                 │
│   ────────────────                      ───────────────────                 │
│                                                                             │
│   02-bundle-dev-actions-manual.yaml     CI-ubereats-automated.yaml          │
│   └─ Lesson 02 Bundle (dev-cicd)        └─ Push: Unit Tests                 │
│                                         └─ PR: Bundle Validate              │
│                                                                             │
│   03-bundle-prod-actions-manual.yaml    CD-ubereats-automated.yaml          │
│   └─ Lesson 03 Bundle (prod)            └─ Merge: Tests → Deploy → App      │
│                                                                             │
│   Test-E2E-ubereats-pipeline.yaml                                           │
│   └─ Full E2E: Deploy → Run → Destroy                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Required GitHub Secrets

Configure these secrets in your repository: **Settings → Secrets → Actions**

| Secret | Description |
|--------|-------------|
| `ARM_CLIENT_ID` | Service Principal Application ID |
| `ARM_CLIENT_SECRET` | Service Principal Client Secret |
| `ARM_TENANT_ID` | Azure Tenant ID |

> **Note:** `DATABRICKS_HOST` is defined as an environment variable in each workflow, not as a secret.

---

## Workflow Details

### 1. `02-bundle-dev-actions-manual.yaml`

**Purpose:** Manual deployment of the Lesson 02 bundle (single environment).

**Trigger:** Manual dispatch only (`workflow_dispatch`)

**Target Bundle:** `02-ubear-eats-bundle-01-env`

**Actions Available:**
- `validate` - Validates bundle configuration
- `deploy` - Deploys to `dev-cicd` target
- `destroy` - Removes all deployed resources

```yaml
env:
  DAB_DIR: "02-ubear-eats-bundle-01-env"
  DATABRICKS_HOST: https://adb-xxx.azuredatabricks.net
```

**Flow:**

```text
┌──────────┐     ┌─────────┐     ┌─────────┐
│ Validate │ ──▶ │ Deploy? │ ──▶ │ Destroy?│
│ (always) │     │ (if set)│     │ (if set)│
└──────────┘     └─────────┘     └─────────┘
```

> ⚠️ **Attention:** If you rename the `02-ubear-eats-bundle-01-env` folder, update `DAB_DIR` in this workflow.

---

### 2. `03-bundle-prod-actions-manual.yaml`

**Purpose:** Manual deployment of the Lesson 03 bundle to production.

**Trigger:** Manual dispatch only (`workflow_dispatch`)

**Target Bundle:** `03-uber-eats-bundles-multi-env`

**Actions Available:**
- `validate` - Validates bundle for `prod` target
- `deploy` - Deploys bundle + starts dashboard app
- `destroy` - Removes all production resources

**Deploy Flow:**

```text
┌──────────────────────────────────────────────────────────┐
│                    DEPLOY ACTION                          │
│                                                          │
│  1. databricks bundle deploy -t prod                     │
│  2. databricks bundle run -t prod ubereats_dashboard     │
│                                                          │
│  (Pipeline run commented out - enable if not continuous) │
└──────────────────────────────────────────────────────────┘
```

> ⚠️ **Attention:** If you rename the `03-uber-eats-bundles-multi-env` folder, update `DAB_DIR` in this workflow.

---

### 3. `CI-ubereats-automated.yaml`

**Purpose:** Continuous Integration - validates changes on every push and PR.

**Triggers:**
- **Push to any branch:** Runs unit tests
- **Pull Request to `main`:** Runs bundle validation

**Target Bundle:** `03-uber-eats-bundles-multi-env`

**Path Filter:** Only triggers on changes to bundle directory or workflow file.

**Flow:**

```text
┌─────────────────────────────────────────────────────────┐
│                   CI WORKFLOW                            │
│                                                         │
│   ON PUSH (any branch):                                 │
│   ┌─────────────────────────────────────────┐           │
│   │ Unit Tests (Python/Pytest)              │           │
│   │ - Setup Python 3.12                     │           │
│   │ - Install test dependencies             │           │
│   │ - Run: pytest tests/unit -v             │           │
│   └─────────────────────────────────────────┘           │
│                                                         │
│   ON PULL REQUEST (to main):                            │
│   ┌─────────────────────────────────────────┐           │
│   │ Bundle Validate                         │           │
│   │ - Setup Databricks CLI                  │           │
│   │ - Validate: databricks bundle validate  │           │
│   └─────────────────────────────────────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### 4. `CD-ubereats-automated.yaml`

**Purpose:** Continuous Deployment - deploys to production when PR is merged.

**Trigger:** Pull Request closed (merged) to `main`

**Target Bundle:** `03-uber-eats-bundles-multi-env`

**Condition:** Only runs if `github.event.pull_request.merged == true`

**Flow:**

```text
┌─────────────────────────────────────────────────────────┐
│                   CD WORKFLOW                            │
│                                                         │
│   ┌────────────┐    ┌────────────┐    ┌──────────────┐  │
│   │ 1. Unit    │───▶│ 2. Bundle  │───▶│ 3. Deploy    │  │
│   │    Tests   │    │    Validate│    │    to Prod   │  │
│   └────────────┘    └────────────┘    └──────┬───────┘  │
│                                              │          │
│                                              ▼          │
│                                       ┌──────────────┐  │
│                                       │ 4. Start     │  │
│                                       │    Dashboard │  │
│                                       └──────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### 5. `Test-E2E-ubereats-pipeline.yaml`

**Purpose:** Full end-to-end testing with automatic cleanup.

**Trigger:** Manual dispatch only (`workflow_dispatch`)

**Target Bundle:** `03-uber-eats-bundles-multi-env`

**Concurrency:** Uses `concurrency` group to prevent parallel runs:

```yaml
concurrency:
  group: e2e-ubereats-dev-cicd
  cancel-in-progress: false
```

**Flow:**

```text
┌─────────────────────────────────────────────────────────┐
│                   E2E TEST WORKFLOW                      │
│                                                         │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐    │
│   │ 1. Unit    │───▶│ 2. Validate│───▶│ 3. Deploy  │    │
│   │    Tests   │    │    Bundle  │    │    Bundle  │    │
│   └────────────┘    └────────────┘    └─────┬──────┘    │
│                                             │           │
│                                             ▼           │
│                                       ┌────────────┐    │
│                                       │ 4. Run     │    │
│                                       │    Pipeline│    │
│                                       └─────┬──────┘    │
│                                             │           │
│                                             ▼           │
│                                       ┌────────────┐    │
│                                       │ 5. Destroy │    │
│                                       │ (always)   │    │
│                                       └────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key Feature:** The destroy step runs with `if: always()`, ensuring cleanup even if previous steps fail.

---

## Workflow Comparison

| Workflow | Trigger | Target | Destroy After? | Use Case |
|----------|---------|--------|----------------|----------|
| `02-bundle-dev-manual` | Manual | `dev-cicd` | Optional | Lesson 02 testing |
| `03-bundle-prod-manual` | Manual | `prod` | Optional | Production deploy |
| `CI-ubereats-automated` | Push/PR | `dev-cicd` | No | PR validation |
| `CD-ubereats-automated` | Merge | `prod` | No | Production release |
| `Test-E2E-ubereats` | Manual | `dev-cicd` | **Yes (always)** | Full E2E testing |

---

## Authentication Flow

All workflows use **Azure Service Principal** authentication via environment variables:

```yaml
env:
  ARM_CLIENT_ID: ${{ secrets.ARM_CLIENT_ID }}
  ARM_CLIENT_SECRET: ${{ secrets.ARM_CLIENT_SECRET }}
  ARM_TENANT_ID: ${{ secrets.ARM_TENANT_ID }}
```

The Databricks CLI automatically uses these for OAuth authentication against Azure-backed workspaces.

The Service Principal ID is passed to bundles via variable:

```bash
databricks bundle deploy -t dev-cicd \
  --var="service_principal_id=${{ secrets.ARM_CLIENT_ID }}"
```

This enables `run_as` configuration in the bundle:

```yaml
run_as:
  service_principal_name: ${var.service_principal_id}
```

---

## Modifying Workflows

### Changing Bundle Directory

If you rename a bundle folder, update the `DAB_DIR` environment variable:

```yaml
env:
  DAB_DIR: "your-new-folder-name"  # Update this
```

### Changing Workspace Host

Update the `DATABRICKS_HOST` environment variable:

```yaml
env:
  DATABRICKS_HOST: https://your-workspace.azuredatabricks.net
```

### Adding New Workflows

Use this template structure:

```yaml
name: 'Your Workflow Name'

on:
  workflow_dispatch:  # or push/pull_request triggers

env:
  ARM_CLIENT_ID: ${{ secrets.ARM_CLIENT_ID }}
  ARM_CLIENT_SECRET: ${{ secrets.ARM_CLIENT_SECRET }}
  ARM_TENANT_ID: ${{ secrets.ARM_TENANT_ID }}
  DATABRICKS_HOST: https://your-workspace.azuredatabricks.net
  DAB_DIR: "your-bundle-folder"

jobs:
  your-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - name: Your Step
        working-directory: ${{ env.DAB_DIR }}
        run: |
          databricks bundle validate -t your-target \
            --var="service_principal_id=${{ secrets.ARM_CLIENT_ID }}"
```
