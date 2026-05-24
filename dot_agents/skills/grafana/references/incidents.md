# Incidents & Sift Reference

## Table of Contents

- [Incidents](#incidents)
- [Sift Investigations](#sift-investigations)
- [Assertions](#assertions)

## Incidents

### List incidents

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_incidents '{"status":"active","limit":10}'
```

### Get incident details

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_incident '{"id":"..."}'
```

**Returns:** Title, status, severity, labels, timestamps, metadata

### Create incident (use sparingly - notifies people)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py create_incident '{"title":"Database connection failures","severity":"critical","roomPrefix":"inc","status":"active"}'
```

Optional fields: `isDrill`, `labels`, `attachUrl`, `attachCaption`

### Add activity to incident

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py add_activity_to_incident '{"incidentId":"...","body":"Identified root cause: connection pool exhaustion. Link: https://..."}'
```

URLs in body are automatically attached as context.

## Sift Investigations

Sift is AI-powered investigation that analyzes logs, traces, and metrics.

### List investigations

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_sift_investigations '{"limit":10}'
```

### Get investigation

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_sift_investigation '{"id":"uuid-string"}'
```

### Get specific analysis

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_sift_analysis '{"investigationId":"uuid","analysisId":"uuid"}'
```

### Find error patterns in logs

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py find_error_pattern_logs '{"name":"API errors investigation","labels":{"service":"api","namespace":"prod"}}'
```

Compares error patterns to last day's average. Returns patterns found.

### Find slow requests

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py find_slow_requests '{"name":"Slow API requests","labels":{"service":"api"}}'
```

Searches Tempo datasources for slow traces.

## Assertions

### Get assertion summary

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_assertions '{"entityType":"Service","entityName":"api","env":"prod","namespace":"default","startTime":"2024-01-01T00:00:00Z","endTime":"2024-01-01T01:00:00Z"}'
```

## Common Patterns

### Investigate production issue

1. `find_error_pattern_logs` - Find elevated error patterns
2. `find_slow_requests` - Check for latency issues
3. Review results and correlate
4. Create incident if needed with `create_incident`
5. Add findings with `add_activity_to_incident`

### Quick health check

1. `list_incidents` with status "active" - Check open incidents
2. `list_alert_rules` filtered by firing state
3. Review Sift investigations if any

## Tool Reference

### list_incidents

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| status | | string | "active" or "resolved" |
| limit | | int | Max results |
| drill | | bool | Include drill incidents |

### create_incident

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| title | ✅ | string | Incident title |
| severity | ✅ | string | critical, major, minor |
| roomPrefix | ✅ | string | e.g., "inc" |
| status | | string | Default: active |
| isDrill | | bool | Drill incident |
| labels | | array | Labels |

### find_error_pattern_logs

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| name | ✅ | string | Investigation name |
| labels | ✅ | object | e.g., {"service":"api"} |
| start | | datetime | ISO 8601 |
| end | | datetime | ISO 8601 |

### find_slow_requests

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| name | ✅ | string | Investigation name |
| labels | ✅ | object | e.g., {"service":"api"} |
