# OnCall Reference

## Table of Contents

- [Schedules](#schedules)
- [Users & Teams](#users--teams)
- [Alert Groups](#alert-groups)
- [Shifts](#shifts)

## Schedules

### List schedules

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_oncall_schedules '{}'
```

With team filter:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_oncall_schedules '{"teamId":"..."}'
```

**Returns:** ID, name, team ID, timezone, shift IDs

### Get current on-call users

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_current_oncall_users '{"scheduleId":"..."}'
```

**Returns:** Schedule info + list of users currently on-call

## Users & Teams

### List OnCall users

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_oncall_users '{}'
```

Filter by username:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_oncall_users '{"username":"..."}'
```

### List OnCall teams

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_oncall_teams '{}'
```

### List Grafana teams (different from OnCall teams)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_teams '{"query":"..."}'
```

### List org users

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_users_by_org '{}'
```

## Alert Groups

### List alert groups

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_alert_groups '{"state":"new"}'
```

Filter options:

- `id`, `integrationId`, `routeId`, `teamId`
- `state`: new | acknowledged | resolved | silenced
- `startedAt`: ISO range format `2024-01-01T00:00:00_2024-01-01T23:59:59`
- `labels`: `["env:prod", "severity:high"]`
- `name`

### Get alert group details

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_alert_group '{"alertGroupId":"..."}'
```

## Shifts

### Get shift details

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_oncall_shift '{"shiftId":"..."}'
```

**Returns:** Time period, assigned users, schedule info

## Common Patterns

### Find who's on-call now

1. `list_oncall_schedules` - Find relevant schedule
2. `get_current_oncall_users` - Get current on-call

### Review alert group for incident

1. `list_alert_groups` with state "new" - Find unacknowledged
2. `get_alert_group` - Get full details
3. Check labels and routing info

### Check team coverage

1. `list_oncall_teams` - Find team
2. `list_oncall_schedules` with teamId - Get team's schedules
3. Review shifts for gaps

## Tool Reference

### list_oncall_schedules

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| teamId | | string | Filter by team |
| scheduleId | | string | Specific schedule |
| page | | int | Pagination |

### get_current_oncall_users

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| scheduleId | ✅ | string | Schedule ID |

### list_alert_groups

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| state | | string | new, acknowledged, resolved, silenced |
| teamId | | string | Filter by team |
| startedAt | | string | ISO range: start_end |
| labels | | array | ["env:prod"] |
| page | | int | Pagination |
