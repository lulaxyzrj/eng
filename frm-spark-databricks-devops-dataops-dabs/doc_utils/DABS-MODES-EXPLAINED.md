# Understanding Modes in Databricks Asset Bundles

The `mode` property in Databricks Asset Bundles is not just a label—it's an **architectural switch** that governs operational behavior, safety protocols, and lifecycle management of deployed resources.

---

## The Two Modes

```text
┌────────────────────────────────────┬────────────────────────────────────┐
│       mode: development            │       mode: production             │
├────────────────────────────────────┼────────────────────────────────────┤
│  Designed for: Agility & Isolation │  Designed for: Stability & Gov.   │
│  Safe iteration in shared spaces   │  Strict standards for data safety │
│  Rapid deploy → test → destroy     │  Canonical, long-lived resources  │
└────────────────────────────────────┴────────────────────────────────────┘
```

---

## Development Mode (`mode: development`)

Designed for **agility and isolation**, this mode prioritizes safe iteration within shared workspaces.

### Key Behaviors

| Feature | Behavior |
|---------|----------|
| **Resource Naming** | Automatically appends prefixes like `[dev user_name]` to Jobs/Pipelines |
| **Schedule State** | All schedules and triggers deployed in **PAUSED** state by default |
| **Lifecycle** | Optimized for rapid "Deploy → Run → Destroy" cycles |
| **Isolation** | Each developer's resources are namespaced to avoid conflicts |

### When to Use

- Local development and testing
- Feature branch validation
- Proof of Concept work
- CI environments for Pull Request validation

### Example Configuration

```yaml
targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://adb-xxx.azuredatabricks.net
```

---

## Production Mode (`mode: production`)

Designed for **stability and governance**, this mode enforces strict standards to protect data integrity.

### Key Behaviors

| Feature | Behavior |
|---------|----------|
| **Resource Naming** | Resources deployed with **exact defined names** (no prefixes) |
| **Validation** | Enforces checks to prevent unsafe configurations |
| **Source Control** | May require deployments from stable branches (e.g., `main`) |
| **DLT Settings** | Blocks `development: true` in DLT pipelines |

### When to Use

- Production deployments
- Staging environments that mirror production
- Any environment where data durability matters

### Example Configuration

```yaml
targets:
  prod:
    mode: production
    workspace:
      host: https://adb-prod.azuredatabricks.net
      root_path: /Shared/.bundle/${bundle.name}/prod
```

---

## The DLT Pipeline Guardrail

### The Error

```
Error: target with 'mode: production' cannot include a pipeline with 'development: true'
```

### Why This Exists

In Delta Live Tables, the `development: true` setting:
- Disables automatic retries
- Treats checkpoints as volatile
- Optimizes for **low cost** and **fast restarts**

This is acceptable for debugging but **dangerous for critical data**.

### The Conflict

When a target is `mode: production`, the system expects:
- High availability
- Data persistence
- Robust checkpointing
- Automatic retry logic

DABs explicitly **block** a "development" pipeline in a "production" target because it would create a fragile pipeline that cannot recover from failures.

### The Solution

For production targets, ensure your pipeline has `development: false`:

```yaml
resources:
  pipelines:
    order_status_pipeline:
      development: false  # Required for mode: production
```

Or use target-level overrides:

```yaml
targets:
  prod:
    mode: production
    resources:
      pipelines:
        order_status_pipeline:
          development: false  # Override for prod
```

---

## Presets: Fine-Grained Control Without Full Mode

When you don't want full `mode: production` constraints but need control over specific behaviors, use **presets**:

```yaml
targets:
  dev-cicd:
    workspace:
      host: https://adb-xxx.azuredatabricks.net
      root_path: /Shared/.bundle/${bundle.name}/dev
    
    # Instead of mode, use presets for specific controls
    presets:
      name_prefix: "[dev] "              # Custom naming prefix
      pipelines_development: true        # Allow DLT development mode
      trigger_pause_status: PAUSED       # Pause all triggers
```

### Available Presets

| Preset | Effect |
|--------|--------|
| `name_prefix` | Custom prefix for all resource names |
| `pipelines_development` | Set DLT pipelines to development mode |
| `trigger_pause_status` | `PAUSED` or `UNPAUSED` for all triggers |
| `jobs_max_concurrent_runs` | Limit concurrent job runs |
| `tags` | Add tags to all resources |

---

## Mode Selection Decision Tree

```text
                   ┌─────────────────────┐
                   │  Is this production │
                   │  or prod-like env?  │
                   └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │ YES           │               │ NO
              ▼               │               ▼
    ┌─────────────────┐       │     ┌─────────────────────┐
    │ mode: production│       │     │ Is this shared CI?  │
    │ development:    │       │     │ (Service Principal) │
    │   false         │       │     └──────────┬──────────┘
    └─────────────────┘       │                │
                              │     ┌──────────┼──────────┐
                              │     │ YES      │          │ NO
                              │     ▼          │          ▼
                              │  Use presets   │   ┌───────────────┐
                              │  instead of    │   │ mode:         │
                              │  full mode     │   │ development   │
                              │                │   │ (default)     │
                              │                │   └───────────────┘
                              └────────────────┘
```

---

## Summary Table

| Aspect | Development | Production |
|--------|-------------|------------|
| **Resource Naming** | Auto-prefixed (isolated) | Exact names (canonical) |
| **Schedules** | Paused by default | Active |
| **DLT `development`** | Allowed | **Blocked** (must be false) |
| **Intended Lifecycle** | Ephemeral (destroy often) | Persistent |
| **Validation Strictness** | Relaxed | Strict |
| **Typical Users** | Individual developers | CI/CD pipelines |
