# Prometheus Reference

## Table of Contents

- [Querying](#querying)
- [Exploring Metrics](#exploring-metrics)
- [Labels](#labels)

## Querying

### Execute PromQL

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py query_prometheus '{"datasourceUid":"...","expr":"up{job=\"prometheus\"}","startTime":"now-1h","queryType":"range","stepSeconds":60}'
```

**Time formats:**

- Relative: `now`, `now-1h`, `now-30m`, `now-2h45m`
- Absolute: RFC3339 format
- Units: `ns`, `us`, `ms`, `s`, `m`, `h`, `d`

### Instant vs Range

- **Instant**: Single point in time, faster - omit `endTime` and `stepSeconds`
- **Range**: Time series data, requires `stepSeconds`

## Exploring Metrics

### List metric names

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_prometheus_metric_names '{"datasourceUid":"...","regex":".*error.*","limit":100}'
```

### Get metric metadata

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_prometheus_metric_metadata '{"datasourceUid":"...","metric":"http_requests_total"}'
```

Returns: metric type, help text, unit.

## Labels

### List label names

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_prometheus_label_names '{"datasourceUid":"..."}'
```

### Get label values

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_prometheus_label_values '{"datasourceUid":"...","labelName":"job"}'
```

### With label matchers

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_prometheus_label_names '{"datasourceUid":"...","matches":[{"filters":[{"name":"job","type":"=","value":"api"}]}]}'
```

Matcher types: `=`, `!=`, `=~` (regex), `!~` (neg regex)

## Common Patterns

### Find available metrics for a job

1. List label values for `job` to find jobs
2. Query `{job="..."}` to see all metrics
3. Use metadata to understand metric types

### Debug missing data

1. Check if metric exists: `list_prometheus_metric_names`
2. Check label values: `list_prometheus_label_values`
3. Try broader time range or remove filters

## Tool Reference

### query_prometheus

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| datasourceUid | ✅ | string | From list_datasources |
| expr | ✅ | string | PromQL expression |
| startTime | ✅ | string | RFC3339 or relative (now-1h) |
| queryType | ✅ | string | "instant" or "range" |
| endTime | | string | Required for range queries |
| stepSeconds | | int | Required for range queries |

### list_prometheus_metric_names

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| datasourceUid | ✅ | string | |
| regex | | string | Filter pattern |
| limit | | int | Max results (default 100) |
| page | | int | Pagination |

### list_prometheus_label_names

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| datasourceUid | ✅ | string | |
| matches | | array | Label matchers |
| startRfc3339 | | string | Time range start |
| endRfc3339 | | string | Time range end |

### list_prometheus_label_values

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| datasourceUid | ✅ | string | |
| labelName | ✅ | string | Label to get values for |
| matches | | array | Label matchers |
