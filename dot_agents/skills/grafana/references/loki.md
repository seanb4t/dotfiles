# Loki Reference

## Table of Contents

- [Querying Logs](#querying-logs)
- [Log Statistics](#log-statistics)
- [Labels](#labels)
- [LogQL Patterns](#logql-patterns)

## Querying Logs

### Query logs

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py query_loki_logs '{"datasourceUid":"...","logql":"{app=\"nginx\"} |= \"error\"","limit":20,"direction":"backward"}'
```

**Returns:** Array of {timestamp, labels, line/value}

### Direction

- `backward`: Newest first (default)
- `forward`: Oldest first

## Log Statistics

### Check stream size before querying

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py query_loki_stats '{"datasourceUid":"...","logql":"{app=\"nginx\"}"}'
```

**Returns:** {streams, chunks, entries, bytes}

Use this first to understand data volume before running expensive queries.

## Labels

### List label names

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_loki_label_names '{"datasourceUid":"..."}'
```

### List label values

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_loki_label_values '{"datasourceUid":"...","labelName":"app"}'
```

## LogQL Patterns

### Basic selectors

```logql
{app="nginx"}                    # exact match
{app=~"nginx|apache"}            # regex match
{app!="test"}                    # not equal
{namespace="prod", app="api"}    # multiple labels
```

### Line filters

```logql
{app="nginx"} |= "error"         # contains
{app="nginx"} != "debug"         # not contains
{app="nginx"} |~ "error|warn"    # regex match
{app="nginx"} !~ "healthcheck"   # regex not match
```

### Parsing and filtering

```logql
{app="nginx"}
  | json
  | status >= 400
  | line_format "{{.method}} {{.path}} {{.status}}"
```

### Metric queries

```logql
rate({app="nginx"} |= "error" [5m])           # errors per second
count_over_time({app="nginx"}[1h])            # log count
sum by (status) (count_over_time({app="nginx"} | json [1h]))
```

## Common Patterns

### Find errors in last hour

1. Check stats: `query_loki_stats` with `{app="..."}`
2. Query: `{app="..."} |= "error" | json`
3. Increase limit if needed

### Explore available log streams

1. `list_loki_label_names` to see labels
2. `list_loki_label_values` for each interesting label
3. Build selector from discovered labels

## Tool Reference

### query_loki_logs

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| datasourceUid | ✅ | string | From list_datasources |
| logql | ✅ | string | LogQL query |
| limit | | int | Max lines (default 10, max 100) |
| direction | | string | "backward" (default) or "forward" |
| startRfc3339 | | string | Start time |
| endRfc3339 | | string | End time |

### query_loki_stats

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| datasourceUid | ✅ | string | |
| logql | ✅ | string | Label selector only (no filters) |
| startRfc3339 | | string | Default: 1 hour ago |
| endRfc3339 | | string | Default: now |

### list_loki_label_names

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| datasourceUid | ✅ | string | |
| startRfc3339 | | string | |
| endRfc3339 | | string | |

### list_loki_label_values

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| datasourceUid | ✅ | string | |
| labelName | ✅ | string | e.g., "app", "env" |
