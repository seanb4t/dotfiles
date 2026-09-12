# Token Efficiency Design for Grafana Skill

**Date:** 2024-12-24
**Status:** Approved

## Problem

The Grafana skill consumes excessive tokens through:

1. Discovery overhead - runtime `--describe` calls to learn tool schemas
2. Multi-step workflows - sequential calls that accumulate in context
3. Output verbosity - pretty-printed JSON with wrapper structure

## Solution

### 1. Output Format Changes

Update `grafana_mcp.py` with new output options.

**New flags:**

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `--format` | json, yaml, compact | yaml | Output format |
| `--brief` | (flag) | off | Return essential fields only |

**Structural changes:**

- Flatten wrapper: return data directly, errors to stderr
- Exit code 1 on errors

**Example:**

```bash
grafana_mcp.py list_datasources '{}' --brief
```

```yaml
- uid: prometheus-1
  name: Prometheus
  type: prometheus
- uid: loki-1
  name: Loki
  type: loki
```

### 2. Compound Workflows

Add workflow commands that batch common multi-step operations.

#### investigate-logs

Find errors in logs for a service.

```bash
grafana_mcp.py investigate-logs '{"app":"nginx","timeRange":"1h"}'
```

Internal flow:

1. Find Loki datasource (auto-discover)
2. Query stats for `{app="..."}`
3. Query logs with `|= "error"` (limit 20)

Output:

```yaml
datasource: loki-1
timeRange: now-1h to now
stats:
  streams: 3
  entries: 1547
  bytes: 524288
errors:
  count: 23
  sample:
    - "2024-01-15T10:23:45Z connection refused to database"
    - "2024-01-15T10:24:12Z timeout waiting for response"
```

#### investigate-metrics

Check metric health for a job/service.

```bash
grafana_mcp.py investigate-metrics '{"job":"api","metric":"error_rate"}'
```

Internal flow:

1. Find Prometheus datasource
2. Query rate for specified metric
3. Return summary with current value

#### quick-status

Overview of system health.

```bash
grafana_mcp.py quick-status '{}'
```

Internal flow:

1. List active incidents
2. List firing alerts

Output:

```yaml
incidents:
  active: 0
alerts:
  firing: 2
  - "High CPU on api-server-3" (critical)
  - "Disk space low on db-1" (warning)
```

#### find-dashboard

Search and summarize a dashboard.

```bash
grafana_mcp.py find-dashboard '{"query":"api latency"}'
```

Internal flow:

1. Search dashboards
2. Get summary of top match

Output:

```yaml
found: 3 matches
top_match:
  uid: api-latency-overview
  title: API Latency Overview
  folder: Production
  panels: 8
  types: [timeseries, stat, table]
  variables: [environment, service]
  url: https://grafana.example.com/d/api-latency-overview
```

### 3. Pre-baked Tool Schemas

Embed tool schemas in reference files to eliminate `--describe` calls.

**Format per reference file:**

```markdown
## Tool Reference

### tool_name

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| param1 | ✅ | string | Description |
| param2 | | int | Optional param |
```

**Tools to document:**

| Reference File | Tools |
|---------------|-------|
| prometheus.md | query_prometheus, list_prometheus_metric_names, list_prometheus_label_names, list_prometheus_label_values |
| loki.md | query_loki_logs, query_loki_stats, list_loki_label_names, list_loki_label_values |
| dashboards.md | search_dashboards, get_dashboard_summary, get_dashboard_property, update_dashboard |
| alerting.md | list_alert_rules, get_alert_rule_by_uid, create_alert_rule |
| incidents.md | list_incidents, create_incident, find_error_pattern_logs, find_slow_requests |
| oncall.md | list_oncall_schedules, get_current_oncall_users, list_alert_groups |

## Implementation Order

1. **Script: Output formatting** - `--format`, `--brief`, flatten wrappers
2. **Script: Compound workflows** - 4 workflow commands
3. **Docs: Schema tables** - Embed in reference files
4. **Docs: SKILL.md update** - New examples and workflow documentation
5. **Version bump** - Update `marketplace.json` and `plugin.json` to 0.2.0

## Estimated Scope

- `grafana_mcp.py`: ~150-200 lines added
- Reference files: ~20-30 lines each (6 files)
- `SKILL.md`: ~30 lines updated
