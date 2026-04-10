# App & Pipeline Configuration Notes

Quick reference for configuration settings that affect behavior and costs.

---

## Dashboard Refresh Interval

**File:** `src/app/app.py`

```python
# =============================================================================
# CONFIGURATION
# =============================================================================
REFRESH_INTERVAL_SECONDS = 30   # Default: 30 seconds
```

### Behavior

| Value | Behavior | Use Case |
|-------|----------|----------|
| `5` | Near real-time | Demos, live monitoring |
| `30` | Balanced (default) | Normal operation |
| `60+` | Conservative | Cost-sensitive environments |

### Consideration

Lower refresh intervals = more frequent SQL Warehouse queries = higher DBU consumption.

For demos or "near real-time" experience, feel free to set `REFRESH_INTERVAL_SECONDS = 5`. Just be aware of the cost implications in long-running scenarios.

---

## Shadow Traffic Data Generation

### ⚠️ Important Change

The Shadow Traffic generator template (`gen_shadow/azure/uber-eats.json.template`) previously included a **filter** that limited data generation. 

**This filter has been removed** to allow continuous data flow for the pipeline.

### What This Means

| Before (with filter) | After (no filter) |
|---------------------|-------------------|
| Limited data batches | Continuous data stream |
| Controlled volume | Unbounded volume |
| Predictable costs | **Requires attention** |

---

## ⚠️ Cost & Resource Warnings

### When Using `continuous: true` Pipeline

If your pipeline is configured with `continuous: true` (production mode):

```yaml
resources:
  pipelines:
    order_status_pipeline:
      continuous: true   # ← Always-on pipeline
```

**You MUST remember to destroy resources when done:**

```bash
# Always clean up after testing
databricks bundle destroy -t dev-cicd --auto-approve

# Or for production
databricks bundle destroy -t prod --auto-approve
```

### Cost Implications

| Setting | Pipeline | Data Gen | Risk |
|---------|----------|----------|------|
| `continuous: false` | Runs once | Batch | Low |
| `continuous: true` | Always-on | Streaming | **High if forgotten** |

### Checklist Before Leaving

- [ ] Pipeline set to `continuous: false` for dev/testing?
- [ ] Dashboard refresh interval reasonable (30s+)?
- [ ] Resources destroyed after demo/testing?
- [ ] No orphaned pipelines running in workspace?

---

## Quick Commands

```bash
# Check what's deployed
databricks bundle summary -t dev

# Stop and clean everything
databricks bundle destroy -t dev --auto-approve

# Verify nothing is running (check UI)
databricks bundle open -t dev
```

---

## Summary

| Config | Location | Default | Adjustable |
|--------|----------|---------|------------|
| Dashboard refresh | `src/app/app.py` | 30s | Yes |
| Pipeline continuous | `databricks.yml` | Yes | Yes (per target) |
| Shadow traffic filter | `uber-eats.json.template` | Removed | N/A |

**Bottom line:** Understand what you're running. Continuous pipelines + frequent refreshes + unfiltered data = costs that add up quickly. Always `destroy` when done experimenting.