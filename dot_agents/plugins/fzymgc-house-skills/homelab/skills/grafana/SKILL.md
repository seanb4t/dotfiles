---
name: grafana
description: |
  Grafana, Loki, and Prometheus operations for the fzymgc-house Kubernetes cluster.
  Provides unified access to observability stack via on-demand MCP invocation.
  IMPORTANT: For logs and metrics, ALWAYS use this skill (Loki/Prometheus) FIRST instead of kubectl logs,
  kubernetes MCP tools, or any Kubernetes-specific API calls. Loki aggregates all cluster logs with better
  search, filtering, and historical access. Prometheus provides proper metrics with time-series queries.
  Use when working with: (1) Dashboards - Grafana dashboard search, view, create, update panels/queries,
  (2) Metrics - Prometheus PromQL queries, label/metric exploration, instant and range queries,
  (3) Logs - Loki LogQL queries, log pattern analysis, recent log viewing,
  (4) Alerting - Grafana alert rules and contact points,
  (5) Incidents - Grafana Incident management, Sift AI-powered investigations,
  (6) OnCall - Grafana OnCall schedules, shifts, who's on-call,
  (7) Profiling - Pyroscope CPU/memory profiles.
  Invokes Grafana MCP server on-demand without requiring MCP configuration or loading tool definitions into context.
metadata:
  author: fzymgc-house
  version: 0.1.0 # x-release-please-version
---

# Grafana Operations

> **⚠️ ALWAYS USE LOKI/PROMETHEUS FIRST**
>
> When investigating logs or metrics, **DO NOT** use `kubectl logs`, Kubernetes MCP tools, or direct Kubernetes API calls.
> Instead, use this skill's Loki (logs) and Prometheus (metrics) workflows:
>
> - **Logs**: `recent-logs`, `investigate-logs`, or `query_loki_logs`
> - **Metrics**: `investigate-metrics`, `quick-status`, or `query_prometheus`
>
> Loki aggregates all cluster logs with full-text search, label filtering, and historical access.
> Prometheus provides proper time-series metrics with PromQL queries.

## Gateway Script

All operations use the gateway script at `${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py`.

### Commands

```bash
# Discovery
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list-tools
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py describe <tool_name>

# Tool invocation (raw MCP tools use JSON)
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py <tool_name> '<json_arguments>'

# Compound workflows (recommended - use CLI flags)
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py investigate-logs --app nginx --time-range 1h
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py investigate-metrics --job api --metric http_requests_total
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py quick-status
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py find-dashboard "api latency"
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py recent-logs --minutes 5 --app nginx
```

### Output Options

```bash
--format yaml    # YAML output (default)
--format json    # Compact JSON
--format compact # Minimal output
--brief          # Essential fields only
```

## Quick Reference

| Task | Start With |
|------|------------|
| Investigate issue | [Investigate](#investigate-an-issue) |
| Explore data | [Explore](#explore-available-data) |
| Manage dashboards | [Dashboards](#manage-dashboards) |
| Set up alerting | [Alerting](#set-up-alerting) |
| Handle incidents | [Incidents](#handle-incidents) |
| Check on-call | [OnCall](#check-on-call) |

## Compound Workflows

**PREFER these over raw MCP tools** - they handle datasource discovery, time formatting,
and multi-step operations automatically. Only use raw tools (e.g., `query_loki_logs`,
`query_prometheus`) when workflows don't meet your specific needs:

### investigate-logs

Find errors in Loki logs for an application:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py investigate-logs --app nginx --time-range 1h --pattern error
```

Options: `--app`, `--namespace`, `--time-range` (default: 1h), `--pattern`

### investigate-metrics

Check Prometheus metric health:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py investigate-metrics --job api --metric http_requests_total
```

Options: `--job`, `--metric`, `--time-range` (default: 1h)

### quick-status

System health overview from Prometheus/Loki:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py quick-status
```

### find-dashboard

Search Grafana dashboards:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py find-dashboard "api latency"
```

### recent-logs

View recent Loki logs (cluster-wide or filtered):

```bash
# Last 5 minutes of all cluster logs
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py recent-logs

# Last 10 minutes for a specific app (by app.kubernetes.io/name)
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py recent-logs --minutes 10 --app nginx

# Filter by namespace
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py recent-logs --minutes 5 --namespace monitoring

# Arbitrary label filters (repeatable)
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py recent-logs --minutes 5 --label pod=nginx-abc123

# Combine filters with line pattern matching
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py recent-logs --minutes 5 --app api --filter error --limit 100
```

Options: `--minutes` (default: 5), `--app`, `--namespace`, `--label KEY=VALUE` (repeatable), `--filter`, `--limit` (default: 50)

## Core Workflows

### Investigate an Issue

1. **Find relevant datasources**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_datasources '{"type":"loki"}'
   ```

2. **Check log patterns** (Loki)

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py query_loki_stats '{"datasourceUid":"...","logql":"{app=\"...\"}"}'
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py query_loki_logs '{"datasourceUid":"...","logql":"{app=\"...\"} |= \"error\"","limit":20}'
   ```

3. **Check metrics** (Prometheus)

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py query_prometheus '{"datasourceUid":"...","expr":"rate(errors[5m])","startTime":"now-1h","queryType":"range","stepSeconds":60}'
   ```

4. **Use Sift for AI analysis**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py find_error_pattern_logs '{"name":"Investigation","labels":{"service":"..."}}'
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py find_slow_requests '{"name":"Latency check","labels":{"service":"..."}}'
   ```

For detailed query syntax: [loki.md](references/loki.md), [prometheus.md](references/prometheus.md)

### Explore Available Data

1. **List datasources**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_datasources '{}'
   ```

2. **Discover labels/metrics**

   ```bash
   # Prometheus
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_prometheus_label_names '{"datasourceUid":"..."}'
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_prometheus_metric_names '{"datasourceUid":"..."}'

   # Loki
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_loki_label_names '{"datasourceUid":"..."}'
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_loki_label_values '{"datasourceUid":"...","labelName":"app"}'
   ```

3. **Find existing dashboards**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py search_dashboards '{"query":"..."}'
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_dashboard_summary '{"uid":"..."}'
   ```

### Manage Dashboards

1. **Find dashboard**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py search_dashboards '{"query":"..."}'
   ```

2. **Understand structure**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_dashboard_summary '{"uid":"..."}'
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_dashboard_panel_queries '{"uid":"..."}'
   ```

3. **Modify with patches**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py update_dashboard '{"uid":"...","operations":[...],"message":"..."}'
   ```

For full operations: [dashboards.md](references/dashboards.md)

### Set Up Alerting

1. **Review existing rules**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_alert_rules '{"limit":20}'
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_contact_points '{}'
   ```

2. **Create new rule** - use `--describe create_alert_rule` to see required parameters

For alert configuration: [alerting.md](references/alerting.md)

### Handle Incidents

1. **Check active incidents**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_incidents '{"status":"active"}'
   ```

2. **Create incident** (notifies people - confirm first)

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py create_incident '{"title":"...","severity":"...","roomPrefix":"inc"}'
   ```

3. **Add investigation notes**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py add_activity_to_incident '{"incidentId":"...","body":"Findings..."}'
   ```

For incident management: [incidents.md](references/incidents.md)

### Check On-Call

1. **Find who's on-call**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_oncall_schedules '{}'
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_current_oncall_users '{"scheduleId":"..."}'
   ```

2. **Review alert groups**

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_alert_groups '{"state":"new"}'
   ```

For on-call operations: [oncall.md](references/oncall.md)

## Tool Discovery

When unsure about tool parameters:

```bash
# List all available tools
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list-tools

# Get tool schema and description
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py describe <tool_name>
```

## Domain References

Load these as needed for detailed operations:

- [dashboards.md](references/dashboards.md) - Dashboard CRUD, panel queries, deeplinks
- [prometheus.md](references/prometheus.md) - PromQL queries, metrics exploration
- [loki.md](references/loki.md) - LogQL queries, log analysis
- [alerting.md](references/alerting.md) - Alert rules, contact points
- [incidents.md](references/incidents.md) - Incident management, Sift investigations
- [oncall.md](references/oncall.md) - Schedules, shifts, users
- [pyroscope.md](references/pyroscope.md) - CPU/memory profiling

## Best Practices

- **Prefer workflows over raw tools**: Use `recent-logs` instead of manual
  `query_loki_logs`, `investigate-logs` instead of hand-crafting Loki queries, etc.
  Workflows handle datasource discovery, time formatting, and label normalization
  automatically
- **Use `describe`** before calling unfamiliar raw tools to see required parameters
- **Query stats before logs**: Use `query_loki_stats` to check volume before `query_loki_logs`
- **Use dashboard summary**: Prefer `get_dashboard_summary` over full `get_dashboard_by_uid`
- **Patch don't replace**: Use `update_dashboard` with `operations` for targeted changes
- **Confirm incident creation**: Creating incidents notifies people - always confirm first
