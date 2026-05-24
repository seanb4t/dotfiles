# Alerting Reference

## Table of Contents

- [Alert Rules](#alert-rules)
- [Contact Points](#contact-points)
- [Alert States](#alert-states)

## Alert Rules

### List alert rules

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_alert_rules '{"limit":100}'
```

With label filter:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_alert_rules '{"label_selectors":[{"filters":[{"name":"severity","type":"=","value":"critical"}]}]}'
```

**Returns:** UID, title, state, labels

### Get rule details

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_alert_rule_by_uid '{"uid":"..."}'
```

**Returns:** Full config including condition, queries, thresholds, annotations

### Create alert rule

Use `--describe create_alert_rule` to see full schema. Key parameters:

- `title`, `ruleGroup`, `folderUID`, `orgID`
- `condition` - query ref that triggers (e.g., "B")
- `data` - array of query configs
- `noDataState`, `execErrState` - NoData | Alerting | OK
- `for` - duration before firing (e.g., "5m")
- `labels`, `annotations`

### Update alert rule

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py update_alert_rule '{"uid":"...","title":"...","ruleGroup":"...",...}'
```

### Delete alert rule

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py delete_alert_rule '{"uid":"..."}'
```

## Contact Points

### List contact points

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_contact_points '{"limit":100}'
```

**Returns:** UID, name, type (email, slack, pagerduty, etc.)

## Alert States

| State | Meaning |
|-------|---------|
| `inactive` | Normal, not firing |
| `pending` | Condition met, waiting for `for` duration |
| `firing` | Alert is active |
| `NoData` | No data received |
| `Error` | Query execution failed |

## Common Patterns

### Find all firing alerts

1. List rules with state filter
2. Get details for firing rules

### Create threshold alert

1. Create data query (refId: "A")
2. Create reduce expression (refId: "B")
3. Create threshold condition (refId: "C")
4. Set condition: "C"

## Tool Reference

### list_alert_rules

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| limit | | int | Default 100 |
| page | | int | Pagination |
| label_selectors | | array | Filter by labels |

### get_alert_rule_by_uid

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| uid | ✅ | string | Alert rule UID |

### create_alert_rule

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| title | ✅ | string | Rule name |
| ruleGroup | ✅ | string | Group name |
| folderUID | ✅ | string | Folder UID |
| condition | ✅ | string | Query ref (e.g., "B") |
| data | ✅ | array | Query configs |
| noDataState | ✅ | string | NoData, Alerting, OK |
| execErrState | ✅ | string | NoData, Alerting, OK |
| for | ✅ | string | Duration (e.g., "5m") |
| orgID | ✅ | int | Organization ID |
