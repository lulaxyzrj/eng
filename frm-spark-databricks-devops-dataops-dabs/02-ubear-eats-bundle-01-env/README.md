# Write# Lesson 02: Custom DLT Pipeline (Single Environment)

Build a real data pipeline with Delta Live Tables using UberEats Shadow Traffic data. This lesson focuses on **separating code from configuration** using proper bundle patterns.

---

## 🎯 Learning Objectives

- Build a custom DLT pipeline from scratch (not from template)
- Externalize configuration into separate `config/` files
- Understand variable substitution in YAML
- Pass configuration to pipeline code via `spark.conf`
- Introduction to CI/CD with GitHub Actions

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DLT PIPELINE FLOW                                   │
│                                                                             │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                 │
│   │   Landing   │ ───▶ │   Bronze    │ ───▶ │   Silver    │ ───▶ Gold       │
│   │   (ADLS)    │      │   (Raw)     │      │  (Cleaned)  │                 │
│   └─────────────┘      └─────────────┘      └─────────────┘                 │
│                                                                             │
│   Configuration Flow:                                                       │
│   databricks.yml → config/variables.yml → resources/pipelines/*.yml → src/  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Bundle Structure

```text
02-ubear-eats-bundle-01-env/
├── databricks.yml                    # Main bundle config (targets)
├── config/
│   └── variables.yml                 # Externalized variables
├── resources/
│   └── pipelines/
│       └── order_status.yml          # DLT pipeline definition
├── src/
│   ├── bronze/
│   │   └── order_status.py           # Bronze layer (ingestion)
│   ├── silver/
│   │   └── order_status.py           # Silver layer (cleaning)
│   └── gold/
│       └── order_status.py           # Gold layer (aggregation)
├── fixtures/                         # Test data (if needed)
├── tests/
│   └── conftest.py
└── pyproject.toml
```

---

## Configuration Deep Dive

### `databricks.yml` - Main Configuration

```yaml
bundle:
  name: ubereats_order_status_01
  databricks_cli_version: ">= 0.218.0"

include:
  - config/*.yml           # ← Load variables from config/
  - resources/**/*.yml     # ← Load all resource definitions

targets:
  # Local development - your personal workspace path
  dev:
    mode: development
    default: true
    workspace:
      host: https://adb-xxx.azuredatabricks.net  # ← Update!

  # CI/CD - shared path via Service Principal
  dev-cicd:
    workspace:
      host: https://adb-xxx.azuredatabricks.net  # ← Update!
      root_path: /Shared/.bundle/${bundle.name}/dev
    
    run_as:
      service_principal_name: ${var.service_principal_id}
    
    presets:
      name_prefix: "[dev] "
      pipelines_development: true
      trigger_pause_status: PAUSED

variables:
  service_principal_id:
    description: "Service Principal Application ID"
    default: ""
```

### `config/variables.yml` - Externalized Variables

```yaml
variables:
  # Storage Configuration
  storage_account:
    description: "Azure Storage Account name for ADLS Gen2"
    default: "adlsubereatsdevsji8"           # ← Update!
  
  landing_container:
    description: "Container name for landing zone"
    default: "landing"

  # Unity Catalog Configuration
  catalog:
    description: "Unity Catalog name"
    default: "ubereats_dev"                   # ← Update if different
  
  bronze_schema:
    description: "Bronze layer schema"
    default: "bronze"
  
  silver_schema:
    description: "Silver layer schema"
    default: "silver"
  
  gold_schema:
    description: "Gold layer schema"
    default: "gold"
```

### `resources/pipelines/order_status.yml` - Pipeline Definition

```yaml
resources:
  pipelines:
    order_status_pipeline:
      name: "[${bundle.target}] Order Status Pipeline"
      
      # Unity Catalog target
      catalog: ${var.catalog}
      schema: ${var.bronze_schema}
      
      # Configuration passed to notebooks via spark.conf
      configuration:
        "pipeline.storage_account": ${var.storage_account}
        "pipeline.landing_container": ${var.landing_container}
        "pipeline.landing_path": "abfss://${var.landing_container}@${var.storage_account}.dfs.core.windows.net"
        "pipeline.catalog": ${var.catalog}
        "pipeline.bronze_schema": ${var.bronze_schema}
        "pipeline.silver_schema": ${var.silver_schema}
        "pipeline.gold_schema": ${var.gold_schema}

      # Pipeline settings
      development: true
      continuous: false
      serverless: true
      photon: true
      
      # Source code
      libraries:
        - notebook:
            path: ../../src/bronze/order_status.py
        - notebook:
            path: ../../src/silver/order_status.py
        - notebook:
            path: ../../src/gold/order_status.py
```

---

## Variable Substitution Flow

```text
┌──────────────────────────────────────────────────────────────────┐
│                    VARIABLE RESOLUTION                           │
│                                                                  │
│   1. config/variables.yml defines defaults:                      │
│      storage_account: "adlsubereatsdevsji8"                      │
│                                                                  │
│   2. resources/pipelines/order_status.yml uses variables:        │
│      "pipeline.storage_account": ${var.storage_account}          │
│                                                                  │
│   3. Pipeline receives configuration:                            │
│      spark.conf.get("pipeline.storage_account")                  │
│      → "adlsubereatsdevsji8"                                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Required Configuration Updates

Before deploying, update these values to match your infrastructure:

| File | Setting | Description |
|------|---------|-------------|
| `databricks.yml` | `workspace.host` | Your workspace URL |
| `config/variables.yml` | `storage_account` | Your ADLS Gen2 account name |
| `config/variables.yml` | `catalog` | Your Unity Catalog name |

---

## Deployment Commands

### Local Development

```bash
cd 02-ubear-eats-bundle-01-env

# Validate
databricks bundle validate -t dev

# Deploy
databricks bundle deploy -t dev

# Run pipeline
databricks bundle run -t dev order_status_pipeline

# Check deployed resources
databricks bundle summary -t dev
```

### CI/CD (via GitHub Actions)

The workflow `02-bundle-dev-actions-manual.yaml` handles deployment:

```bash
# From GitHub Actions UI:
# 1. Go to Actions → "Testing Bundle Dev Actions"
# 2. Click "Run workflow"
# 3. Select action: validate / deploy / destroy
```

---

## Understanding the Two Targets

### `dev` - Local Development

```yaml
dev:
  mode: development
  default: true
```

- Uses your personal credentials (PAT)
- Workspace path: `/Users/your-email/.bundle/...`
- Resources prefixed with `[dev your_name]`

### `dev-cicd` - CI/CD Environment

```yaml
dev-cicd:
  workspace:
    root_path: /Shared/.bundle/${bundle.name}/dev
  run_as:
    service_principal_name: ${var.service_principal_id}
```

- Uses Service Principal credentials
- Workspace path: `/Shared/.bundle/...`
- Shared deployment for the team

---

## GitHub Actions Introduction

This lesson introduces the first CI/CD workflow:

**File:** `.github/workflows/02-bundle-dev-actions-manual.yaml`

```yaml
name: 'Testing Bundle Dev Actions [Manual-02-bundle-dev]'

on:
  workflow_dispatch:
    inputs:
      action:
        type: choice
        options:
          - validate
          - deploy
          - destroy
```

This is a **manual workflow** - you trigger it from the GitHub UI to:
- **validate**: Check configuration
- **deploy**: Push to `dev-cicd` target
- **destroy**: Clean up resources

👉 **[Workflows Documentation](../doc_utils/GITHUB-WORKFLOWS-EXPLAINED.md)**

---

## Why Separate Code from Configuration?

| Approach | Problem |
|----------|---------|
| Hardcoded values in code | Can't change without code change |
| Environment variables only | Hard to audit, easy to misconfigure |
| **Bundle variables** | ✅ Auditable, versionable, validated |

By externalizing to `config/variables.yml`:
- Configuration is **reviewable** in PRs
- Same code works across environments
- Clear separation of concerns

---

## Clean Up

```bash
# Local
databricks bundle destroy -t dev

# CI/CD (via GitHub Actions)
# Run workflow with action: destroy
```

---

## Next Steps

Once comfortable with single-environment deployment:
👉 **[Go to Lesson 03: Multi-Environment + Automation](../03-uber-eats-bundles-multi-env/README.md)**
