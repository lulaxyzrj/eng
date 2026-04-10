# Databricks Asset Bundles: Architecture, Multi-Bundle CI/CD, and Separation of Responsibilities

This guide covers architectural decisions for bundle granularity, multi-bundle repository strategies, and the separation between Terraform (infrastructure) and DABs (workloads).

---

## 1. Bundle Granularity: How Many Assets Per Bundle?

### What the Documentation Says

> "A bundle is an end-to-end definition of a project, including how the project should be structured, tested, and deployed."  
> — [docs.databricks.com/dev-tools/bundles](https://docs.databricks.com/dev-tools/bundles)

There is **no limit** or official recommendation on the number of assets. The focus is the **project**, not a "data product" or "domain".

### Supported Assets

- Jobs (Lakeflow Jobs)
- Pipelines (Lakeflow Declarative Pipelines / DLT)
- MLflow Experiments/Models
- Model Serving Endpoints
- Dashboards
- Unity Catalog Schemas

### Decision Criteria

| Criterion | Same Bundle | Separate Bundles |
|-----------|-------------|------------------|
| **Deploy cadence** | Same release pace | Independent releases |
| **Ownership** | Same team | Different teams |
| **Dependencies** | Tightly coupled | Independent |
| **Permissions** | Same access model | Different access requirements |

### Heuristic

**1 bundle = 1 project with a cohesive lifecycle**

There is no hard limit, no "1 bundle = 1 data product" recommendation, and no penalty for a large bundle.

---

## 2. Repository Structure with Multiple Bundles

### Monorepo Pattern (Official)

```text
databricks-bundle-repo/
├── shared/                          # Shared config and code
│   ├── variables.yml
│   └── shared_library.py
├── job_bundle/                      # Bundle A
│   ├── databricks.yml
│   ├── resources/
│   │   └── job_bundle.job.yml
│   └── src/
│       └── my_python.py
├── pipeline_bundle/                 # Bundle B
│   ├── databricks.yml
│   ├── resources/
│   │   └── pipeline_bundle.pipeline.yml
│   └── src/
│       └── my_pipeline.ipynb
└── .github/workflows/
    └── deploy.yml
```

Source: [Sharing bundles and bundle files](https://docs.databricks.com/dev-tools/bundles/sharing)

### Sharing Config and Code Across Bundles

```yaml
# job_bundle/databricks.yml
bundle:
  name: job_bundle

sync:
  paths:
    - ../shared           # Include shared code
    - ./src

include:
  - resources/*.yml
  - ../shared/*.yml       # Include shared variables

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://my-workspace.cloud.databricks.com
  prod:
    mode: production
    workspace:
      host: https://my-workspace.cloud.databricks.com
```

### Shared Variables File

```yaml
# shared/variables.yml
variables:
  cluster_id:
    default: 1234-567890-abcde123
  notification_email:
    default: alerts@company.com
```

---

## 3. Authentication: Azure AD Service Principal

### Recommendation

Use the **same Service Principal** as Terraform. The Databricks CLI reads `ARM_*` environment variables automatically.

```yaml
env:
  ARM_CLIENT_ID: ${{ secrets.ARM_CLIENT_ID }}
  ARM_CLIENT_SECRET: ${{ secrets.ARM_CLIENT_SECRET }}
  ARM_TENANT_ID: ${{ secrets.ARM_TENANT_ID }}
  ARM_SUBSCRIPTION_ID: ${{ secrets.ARM_SUBSCRIPTION_ID }}
  DATABRICKS_HOST: <from Terraform outputs or hardcoded>
```

### Authentication Methods Comparison

| Method | Secrets Required | Rotation | Recommendation |
|--------|------------------|----------|----------------|
| **Azure AD SP (ARM_*)** | tenant, client_id, secret | Configurable | ✅ Recommended |
| OAuth M2M (Databricks) | client_id, client_secret | Up to 2 years | Good |
| Workload Identity Federation | client_id only | Automatic | Best (if available) |
| PAT (token) | Static token | Manual | ❌ Legacy |

---

## 4. CI/CD with Multiple Bundles

### Selective Deploy Pattern

Deploy only bundles that changed using path filters:

```yaml
name: Selective Bundle Deploy
on:
  push:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      job_bundle: ${{ steps.filter.outputs.job_bundle }}
      pipeline_bundle: ${{ steps.filter.outputs.pipeline_bundle }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            job_bundle:
              - 'job_bundle/**'
              - 'shared/**'
            pipeline_bundle:
              - 'pipeline_bundle/**'
              - 'shared/**'

  deploy-job-bundle:
    needs: detect-changes
    if: needs.detect-changes.outputs.job_bundle == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: databricks bundle validate
        working-directory: ./job_bundle
      - run: databricks bundle deploy -t prod
        working-directory: ./job_bundle

  deploy-pipeline-bundle:
    needs: detect-changes
    if: needs.detect-changes.outputs.pipeline_bundle == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: databricks bundle validate
        working-directory: ./pipeline_bundle
      - run: databricks bundle deploy -t prod
        working-directory: ./pipeline_bundle
```

> **Note:** `dorny/paths-filter` is a third-party action, not official Databricks.

### Dynamic Workspace Host from Terraform

```yaml
jobs:
  get-workspace-config:
    runs-on: ubuntu-latest
    outputs:
      dev_host: ${{ steps.tf.outputs.dev_host }}
      prod_host: ${{ steps.tf.outputs.prod_host }}
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - name: Terraform Init
        working-directory: terraform-infra-cicd/phase-01-azure-infra
        run: |
          terraform init \
            -backend-config="resource_group_name=ubereats-tfstate-rg" \
            -backend-config="storage_account_name=${{ secrets.TF_BACKEND_SA }}" \
            -backend-config="container_name=tfstate" \
            -backend-config="key=phase-01-azure-infra.tfstate"
      - name: Get Terraform Outputs
        id: tf
        run: |
          echo "dev_host=$(terraform output -raw dev_workspace_url)" >> $GITHUB_OUTPUT
          echo "prod_host=$(terraform output -raw prod_workspace_url)" >> $GITHUB_OUTPUT

  deploy-dev:
    needs: get-workspace-config
    env:
      DATABRICKS_HOST: ${{ needs.get-workspace-config.outputs.dev_host }}
    # ... deploy steps
```

---

## 5. Terraform vs. DABs: Separation of Responsibilities

### Terraform — Platform Layer

| Resource Type | Examples |
|---------------|----------|
| **Workspaces** | VNet injection, Private Links |
| **Unity Catalog** | Metastore, Storage Credentials, External Locations |
| **Networking** | Private Endpoints, Firewall rules |
| **Security** | Service Principals, Groups, Role Assignments |

### DABs — Logic and Orchestration Layer

| Resource Type | Examples |
|---------------|----------|
| **Workflows** | Jobs, Tasks, Schedules |
| **Pipelines** | Delta Live Tables |
| **ML** | Experiments, Registered Models, Serving Endpoints |
| **Analytics** | Dashboards |
| **Data** | Unity Catalog Schemas |

### Decision Rule

| Question | Tool |
|----------|------|
| Changes rarely and is a prerequisite for workloads? | **Terraform** |
| Changes frequently alongside code? | **DABs** |
| Owned by Platform/Infra team? | **Terraform** |
| Owned by Data/ML team? | **DABs** |

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RESPONSIBILITY SEPARATION                                 │
│                                                                             │
│   TERRAFORM (Platform Team)              DABs (Data Team)                   │
│   ─────────────────────────              ───────────────────                │
│   • Workspaces                           • Jobs & Schedules                 │
│   • Unity Catalog Metastore              • DLT Pipelines                    │
│   • Storage Credentials                  • ML Experiments                   │
│   • External Locations                   • Dashboards                       │
│   • Service Principals                   • UC Schemas                       │
│   • Networking                           • Code + Config                    │
│                                                                             │
│   Changes: Quarterly                     Changes: Daily/Weekly              │
│   Lifecycle: Long-lived                  Lifecycle: Iterative               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

> ⚠️ **Important:** Do not manage Jobs via Terraform. Terraform has no visibility into the code that Jobs execute. Use DABs to package code + Job definition together.

---

## 6. Implementation Checklist

### Before Creating Bundles

- [ ] Terraform: Workspace provisioned
- [ ] Terraform: Unity Catalog configured (Metastore, Storage Credentials)
- [ ] Service Principal created with proper permissions
- [ ] Decision made: monorepo vs. separate repositories

### For Each Bundle

- [ ] `databricks.yml` at bundle root
- [ ] Targets defined (dev, staging, prod)
- [ ] `mode: development` for non-prod targets
- [ ] `mode: production` + `run_as` for prod target
- [ ] Permissions defined in bundle YAML

### CI/CD Setup

- [ ] GitHub Secrets configured (ARM_* variables)
- [ ] `databricks bundle validate` runs before deploy
- [ ] Environment progression (dev → staging → prod)
- [ ] Concurrency control to prevent parallel deploys

---

## 7. Essential Commands

```bash
# Validate configuration
databricks bundle validate

# Deploy to specific target
databricks bundle deploy -t dev
databricks bundle deploy -t prod

# Run a specific job
databricks bundle run my_job -t dev

# Generate bundle from existing job
databricks bundle generate job --existing-job-id 123456

# Destroy all resources
databricks bundle destroy -t dev
```

---

## 8. Official References

| Resource | URL |
|----------|-----|
| DABs Documentation | https://docs.databricks.com/dev-tools/bundles |
| Bundle Examples (GitHub) | https://github.com/databricks/bundle-examples |
| Terraform Examples (GitHub) | https://github.com/databricks/terraform-databricks-examples |
| GitHub Actions Guide | https://docs.databricks.com/dev-tools/ci-cd/github |
| CI/CD Best Practices | https://docs.databricks.com/dev-tools/ci-cd/best-practices |
| Sharing Bundles | https://docs.databricks.com/dev-tools/bundles/sharing |