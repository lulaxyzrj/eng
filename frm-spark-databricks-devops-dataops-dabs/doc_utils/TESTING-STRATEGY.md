# Testing Strategy for Databricks Asset Bundles

This document covers testing approaches for DABs projects, including unit tests, end-to-end (E2E) tests, and the tradeoffs involved.

---

## Testing Pyramid for DABs

```text
                    ┌───────────────┐
                    │    E2E Tests  │  ← Expensive, Slow, High Confidence
                    │   (Pipeline   │
                    │    Execution) │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  Integration  │  ← Moderate Cost, Validates Configs
                    │    Tests      │
                    │  (Validate +  │
                    │    Deploy)    │
                    └───────┬───────┘
                            │
        ┌───────────────────▼───────────────────┐
        │              Unit Tests               │  ← Cheap, Fast, Run Often
        │  (Python logic, transformations)      │
        └───────────────────────────────────────┘
```

---

## Test Types

### Unit Tests

**What:** Test Python transformation logic in isolation.

**Where:** `tests/unit/`

**When to Run:** On every push, locally during development.

**Cost:** Free (local Python execution)

**Example:**

```python
# tests/unit/test_bronze_layer.py
def test_order_status_schema():
    """Verify expected columns exist"""
    expected_cols = ["order_id", "status", "timestamp"]
    # Test transformation logic
```

**Run locally:**

```bash
cd 03-uber-eats-bundles-multi-env
pip install -r tests/requirements.txt
python -m pytest tests/unit -v
```

---

### Integration Tests (Bundle Validate)

**What:** Verify bundle configuration is syntactically correct and references exist.

**When to Run:** On Pull Requests.

**Cost:** Free (CLI validation, no DBUs consumed)

**Command:**

```bash
databricks bundle validate -t dev-cicd \
  --var="service_principal_id=${{ secrets.ARM_CLIENT_ID }}"
```

---

### End-to-End Tests (E2E)

**What:** Full deployment cycle: Deploy → Run Pipeline → Destroy.

**When to Run:** Sparingly (manual trigger or nightly).

**Cost:** DBUs consumed for pipeline execution.

**Workflow:** `Test-E2E-ubereats-pipeline.yaml`

---

## E2E Test Tradeoffs

Use E2E tests sparingly. Full runs should gate only **high-impact PRs** (feature work, risky refactors), not every small PR.

| Aspect | Tradeoff | Mitigation |
|--------|----------|------------|
| **Time** | Pipeline adds minutes to PR checks | Serverless reduces cold start |
| **Cost** | Each run consumes DBUs | Low volume in course; small datasets |
| **Race Condition** | 2 PRs on same target can collide | `concurrency` group (1 at a time) |
| **Test Data** | Pipeline needs data in landing | Shadow traffic shared in dev |
| **Mid-Run Failure** | Deploy OK but pipeline fails → orphaned resources | `destroy` with `if: always()` |
| **Aggressive Drop** | Drops Unity Catalog tables | OK for `dev-cicd`; prod never uses this flow |

---

## CI vs CD: Why Destroy in CI but Not CD?

| CI (Pull Request) | CD (Merge to Main) |
|-------------------|-------------------|
| Ephemeral environment for validation | Persistent environment |
| Destroy after tests | Deploy only, no destroy |
| Goal: "Does it work?" | Goal: "Deliver at scale" |
| Target: `dev-cicd` | Target: `prod` |

```text
┌─────────────────────────────────────────────────────────┐
│                    CI FLOW (PR)                          │
│                                                         │
│   Deploy ──▶ Run ──▶ Validate ──▶ DESTROY               │
│                                                         │
│   Environment is temporary. Clean up after.             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    CD FLOW (Merge)                       │
│                                                         │
│   Deploy ──▶ Run ──▶ Monitor                            │
│                                                         │
│   Environment is permanent. Keep running.               │
└─────────────────────────────────────────────────────────┘
```

---

## When NOT to Use E2E in PRs

Consider avoiding E2E tests in PR validation when:

- Pipelines are **slow** (>10 minutes)
- Test datasets are **large** (hundreds of MB+)
- DBU cost is a **real concern** (production accounts)
- You need to **keep state** between PRs for debugging

### Alternative: Periodic E2E

Run full E2E of core paths **periodically** (e.g., nightly or weekly) outside the PR flow:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
```

---

## Concurrency Control

To prevent race conditions when multiple PRs trigger E2E tests:

```yaml
concurrency:
  group: e2e-ubereats-dev-cicd
  cancel-in-progress: false  # Queue instead of cancel
```

This ensures only one E2E test runs at a time for the `dev-cicd` target.

---

## Cleanup with `if: always()`

The destroy step should **always run**, even if previous steps fail:

```yaml
destroy:
  name: 5. Destroy Bundle (Cleanup)
  runs-on: ubuntu-latest
  needs: run-pipeline
  if: always()  # ← Critical: runs even on failure
  
  steps:
    - name: Destroy Bundle
      run: |
        databricks bundle destroy -t dev-cicd \
          --var="service_principal_id=${{ secrets.ARM_CLIENT_ID }}" \
          --auto-approve
```

This prevents "zombie resources" that accumulate DBU costs.

---

## Test File Organization

```text
03-uber-eats-bundles-multi-env/
└── tests/
    ├── __init__.py
    ├── pytest.ini            # Pytest configuration
    ├── requirements.txt      # Test dependencies
    └── unit/
        ├── __init__.py
        ├── conftest.py       # Shared fixtures
        └── test_bronze_layer.py
```

### `requirements.txt`

```text
pytest>=7.0.0
pyspark>=3.5.0
delta-spark>=3.0.0
```

### `pytest.ini`

```ini
[pytest]
testpaths = unit
python_files = test_*.py
python_functions = test_*
```

---

## Summary: Testing Recommendations

| Test Type | Run When | Cost | Confidence |
|-----------|----------|------|------------|
| **Unit Tests** | Every push | Free | Low (logic only) |
| **Bundle Validate** | Every PR | Free | Medium (config) |
| **E2E (Full)** | Manual / Nightly | DBUs | High (full flow) |

**Bottom Line:** Invest heavily in unit tests. Use E2E strategically, not on every PR.
