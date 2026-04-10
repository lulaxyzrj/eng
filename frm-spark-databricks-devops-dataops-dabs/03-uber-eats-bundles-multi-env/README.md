# Lesson 03: Multi-Environment Deployment + Automation

Scale to production with multi-environment deployments, unit tests, a Streamlit dashboard app, and fully automated CI/CD pipelines.

---

## 🎯 Learning Objectives

- Configure multi-environment deployments (dev → prod)
- Override variables per target
- Add unit tests to the project
- Deploy a Databricks App (Streamlit dashboard)
- Implement automated CI/CD pipelines

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-ENVIRONMENT ARCHITECTURE                           │
│                                                                             │
│   ┌─────────────────────┐              ┌─────────────────────┐              │
│   │   DEV WORKSPACE     │              │   PROD WORKSPACE    │              │
│   │                     │              │                     │              │
│   │  ┌───────────────┐  │   CI/CD      │  ┌───────────────┐  │              │
│   │  │ DLT Pipeline  │  │ ─────────▶   │  │ DLT Pipeline  │  │              │
│   │  │ (dev-cicd)    │  │              │  │ (prod)        │  │              │
│   │  └───────────────┘  │              │  └───────────────┘  │              │
│   │                     │              │                     │              │
│   │  ┌───────────────┐  │              │  ┌───────────────┐  │              │
│   │  │ Dashboard App │  │              │  │ Dashboard App │  │              │
│   │  └───────────────┘  │              │  └───────────────┘  │              │
│   │                     │              │                     │              │
│   │  catalog: ubereats_ │              │  catalog: ubereats_ │              │
│   │           dev       │              │           prod      │              │
│   │                     │              │                     │              │
│   │  storage account:   │              │  storage account:   │              │
│   │    adlsubereadtsdev │              │    adlsubereats prod│              │
│   └─────────────────────┘              └─────────────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Bundle Structure

```text
03-uber-eats-bundles-multi-env/
├── databricks.yml                    # Multi-target configuration
├── config/
│   └── variables.yml                 # Default + production overrides
├── resources/
│   ├── pipelines/
│   │   └── order_status.yml          # DLT pipeline
│   └── apps/
│       └── app.yml                   # Streamlit dashboard
├── src/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   └── app/                          # Dashboard application
│       ├── app.py
│       ├── app.yaml
│       ├── config.py
│       └── requirements.txt
└── tests/
    ├── pytest.ini
    ├── requirements.txt
    └── unit/
        ├── conftest.py
        └── test_bronze_layer.py
```

---

## Multi-Environment Configuration

### `databricks.yml` - Three Targets

```yaml
bundle:
  name: ubereats_order_status_final
  databricks_cli_version: ">= 0.218.0"

include:
  - config/*.yml
  - resources/**/*.yml

targets:
  # ──────────────────────────────────────────────────────────
  # LOCAL DEVELOPMENT
  # ──────────────────────────────────────────────────────────
  dev:
    mode: development
    default: true
    workspace:
      host: https://adb-xxx.azuredatabricks.net  # ← DEV workspace

  # ──────────────────────────────────────────────────────────
  # CI/CD DEVELOPMENT
  # ──────────────────────────────────────────────────────────
  dev-cicd:
    workspace:
      host: https://adb-xxx.azuredatabricks.net  # ← DEV workspace
      root_path: /Shared/.bundle/${bundle.name}/dev
    
    run_as:
      service_principal_name: ${var.service_principal_id}
    
    presets:
      name_prefix: "[${bundle.target}]"

  # ──────────────────────────────────────────────────────────
  # PRODUCTION
  # ──────────────────────────────────────────────────────────
  prod:
    workspace:
      host: https://adb-yyy.azuredatabricks.net  # ← PROD workspace (different!)
      root_path: /Shared/.bundle/${bundle.name}/prod
    
    run_as:
      service_principal_name: ${var.service_principal_id}

    # VARIABLE OVERRIDES FOR PRODUCTION
    variables:
      catalog: "ubereats_prod"                  # ← Different catalog
      storage_account: "adlsubereatsprodsji8"   # ← Different storage
      warehouse_id: "20b5fe1254385a96"          # ← Different warehouse

    presets:
      name_prefix: "[${bundle.target}]"

    # RESOURCE OVERRIDES FOR PRODUCTION
    resources:
      pipelines:
        order_status_pipeline:
          continuous: true                      # ← Always-on in prod
```

---

## Variable Override Pattern

```text
┌─────────────────────────────────────────────────────────────────┐
│                  VARIABLE RESOLUTION ORDER                       │
│                                                                 │
│   1. CLI flag (highest priority)                                │
│      databricks bundle deploy --var="catalog=test"              │
│                                                                 │
│   2. Target-specific override                                   │
│      targets.prod.variables.catalog: "ubereats_prod"            │
│                                                                 │
│   3. Default value (lowest priority)                            │
│      variables.catalog.default: "ubereats_dev"                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Example in `config/variables.yml`:

```yaml
variables:
  catalog:
    description: "Unity Catalog name"
    default: "ubereats_dev"            # ← Default (dev)

  storage_account:
    description: "Azure Storage Account"
    default: "adlsubereatsdevsji8"     # ← Default (dev)

  warehouse_id:
    description: "SQL Warehouse ID for App"
    default: "74d8cdb4c30f40a2"        # ← Default (dev warehouse)
```

Production overrides in `databricks.yml`:

```yaml
targets:
  prod:
    variables:
      catalog: "ubereats_prod"                 # ← Overrides default
      storage_account: "adlsubereatsprodsji8"  # ← Overrides default
      warehouse_id: "20b5fe1254385a96"         # ← Overrides default
```

---

## ⚠️ Required Configuration Updates

| File | Setting | Dev Value | Prod Value |
|------|---------|-----------|------------|
| `databricks.yml` | `targets.dev.workspace.host` | Your dev URL | - |
| `databricks.yml` | `targets.prod.workspace.host` | - | Your prod URL |
| `databricks.yml` | `targets.prod.variables.catalog` | - | Your prod catalog |
| `databricks.yml` | `targets.prod.variables.storage_account` | - | Your prod storage |
| `databricks.yml` | `targets.prod.variables.warehouse_id` | - | Your prod warehouse |
| `config/variables.yml` | `storage_account.default` | Your dev storage | - |
| `config/variables.yml` | `warehouse_id.default` | Your dev warehouse | - |

---

## Databricks App (Dashboard)

### `resources/apps/app.yml`

```yaml
resources:
  apps:
    ubereats_dashboard:
      name: "ubereats-dashboard-${bundle.target}"
      description: "UberEats Operations Dashboard"
      source_code_path: ../../src/app

      permissions:
        - group_name: data-engineers
          level: CAN_MANAGE

      resources:
        - name: sql_warehouse
          sql_warehouse:
            id: ${var.warehouse_id}
            permission: CAN_USE
```

The app is a Streamlit dashboard that:
- Reads from Gold layer tables
- Displays order funnel metrics
- Shows payment health status

> [!WARNING]
> **[App Configuration Notes](./APP-CONFIGURATION-NOTES.md)**
> Consult this configuration if you aim for **Near Real-Time** latency.
> *Includes critical details on Dashboard refresh, Shadow Traffic, and cost implications.*

---

## Unit Tests

### Test Structure

```text
tests/
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Test dependencies
└── unit/
    ├── conftest.py       # Shared fixtures
    └── test_bronze_layer.py
```

### Running Tests Locally

```bash
cd 03-uber-eats-bundles-multi-env

# Install test dependencies
pip install -r tests/requirements.txt

# Run tests
python -m pytest tests/unit -v
```

---

## CI/CD Pipelines

### Automated Workflows

| Workflow | Trigger | Target | Purpose |
|----------|---------|--------|---------|
| `CI-ubereats-automated.yaml` | Push / PR | `dev-cicd` | Validate & test |
| `CD-ubereats-automated.yaml` | Merge to main | `prod` | Deploy to production |

### Manual Workflows

| Workflow | Trigger | Target | Purpose |
|----------|---------|--------|---------|
| `03-bundle-prod-actions-manual.yaml` | Manual | `prod` | Manual prod deploy |
| `Test-E2E-ubereats-pipeline.yaml` | Manual | `dev-cicd` | Full E2E test |

### CI Flow (On PR)

```text
┌──────────────────────────────────────────┐
│   PULL REQUEST TO MAIN                    │
│                                          │
│   1. Unit Tests (Python)                 │
│   2. Bundle Validate (dev-cicd)          │
│                                          │
│   ✓ PR can be merged if green            │
└──────────────────────────────────────────┘
```

### CD Flow (On Merge)

```text
┌──────────────────────────────────────────┐
│   MERGE TO MAIN                          │
│                                          │
│   1. Unit Tests                          │
│   2. Bundle Validate (prod)              │
│   3. Deploy to Production                │
│   4. Start Dashboard App                 │
│                                          │
│   ✓ Production is updated automatically  │
└──────────────────────────────────────────┘
```

👉 **[Complete Workflows Documentation](../doc_utils/GITHUB-WORKFLOWS-EXPLAINED.md)**

---

## Deployment Commands

### Local Development

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev order_status_pipeline
databricks bundle run -t dev ubereats_dashboard
```

### CI/CD Development

```bash
databricks bundle deploy -t dev-cicd \
  --var="service_principal_id=$ARM_CLIENT_ID"
```

### Production

```bash
databricks bundle deploy -t prod \
  --var="service_principal_id=$ARM_CLIENT_ID"
```

### Full Deploy + Run Sequence

```bash
# Deploy everything
databricks bundle deploy -t dev

# Run pipeline (populates data)
databricks bundle run -t dev order_status_pipeline

# Start dashboard
databricks bundle run -t dev ubereats_dashboard

# Get app URL
databricks bundle summary -t dev
```

---

## Clean Up

```bash
# Development
databricks bundle destroy -t dev

# CI/CD
databricks bundle destroy -t dev-cicd \
  --var="service_principal_id=$ARM_CLIENT_ID" \
  --auto-approve

# Production (careful!)
databricks bundle destroy -t prod \
  --var="service_principal_id=$ARM_CLIENT_ID" \
  --auto-approve
```

---

## Summary: Multi-Env Benefits

| Benefit | How Achieved |
|---------|--------------|
| **Same code, different configs** | Variable overrides per target |
| **Environment isolation** | Separate workspaces, catalogs |
| **Automated validation** | CI pipeline on every PR |
| **Automated deployment** | CD pipeline on merge |
| **Consistent naming** | `${bundle.target}` in resource names |

---

## Reference Documentation

- 👉 **[App Configuration Notes](./APP-CONFIGURATION-NOTES.md)** - Dashboard refresh, Shadow Traffic, cost warnings
- 👉 **[Bundle Architecture Guide](../doc_utils/BUNDLE-ARCHITECTURE-GUIDE.md)**
- 👉 **[DABs Commands](../doc_utils/DABS-COMMANDS.md)**
- 👉 **[Development vs Production Modes](../doc_utils/DABS-MODES-EXPLAINED.md)**
- 👉 **[GitHub Workflows](../doc_utils/GITHUB-WORKFLOWS-EXPLAINED.md)**
- 👉 **[Testing Strategy](../doc_utils/TESTING-STRATEGY.md)**

