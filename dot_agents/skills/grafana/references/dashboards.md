# Dashboards Reference

## Table of Contents

- [Search & Discovery](#search--discovery)
- [Reading Dashboards](#reading-dashboards)
- [Modifying Dashboards](#modifying-dashboards)
- [Folders](#folders)

## Search & Discovery

### Find dashboards

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py search_dashboards '{"query":"..."}'
```

Returns list with title, UID, folder, tags, URL.

### Find folders

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py search_folders '{"query":"..."}'
```

## Reading Dashboards

### Get summary (preferred for overview)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_dashboard_summary '{"uid":"..."}'
```

Returns: title, panel count, types, variables, metadata. Use this first to understand structure.

### Get specific properties (context-efficient)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_dashboard_property '{"uid":"...","jsonPath":"$.panels[*].title"}'
```

Common paths:

- `$.title` - Dashboard title
- `$.panels[*].title` - All panel titles
- `$.panels[0]` - First panel
- `$.templating.list` - Variables
- `$.tags` - Tags
- `$.panels[*].targets[*].expr` - All queries

### Get panel queries

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_dashboard_panel_queries '{"uid":"..."}'
```

Returns array of {title, query, datasource}. Use to understand what data the dashboard visualizes.

### Get full dashboard (use sparingly - large output)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py get_dashboard_by_uid '{"uid":"..."}'
```

## Modifying Dashboards

### Create new dashboard

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py update_dashboard '{"dashboard":{...},"folderUid":"...","message":"commit message"}'
```

### Patch existing dashboard (preferred - context efficient)

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py update_dashboard '{"uid":"...","operations":[{"op":"replace","path":"$.title","value":"New Title"}],"message":"commit message"}'
```

### Common patch operations

- Replace panel title: `{"op":"replace","path":"$.panels[0].title","value":"..."}`
- Update query: `{"op":"replace","path":"$.panels[0].targets[0].expr","value":"..."}`
- Add panel: `{"op":"add","path":"$.panels/-","value":{...}}`

## Folders

### Create folder

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py create_folder '{"title":"...","uid":"...","parentUid":"..."}'
```

### Navigate deeplinks

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py generate_deeplink '{"resourceType":"dashboard","dashboardUid":"...","timeRange":{"from":"now-1h","to":"now"}}'
```

Resource types: `dashboard`, `panel`, `explore`

## Tool Reference

### search_dashboards

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| query | | string | Search term |

### get_dashboard_summary

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| uid | ✅ | string | Dashboard UID |

### get_dashboard_property

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| uid | ✅ | string | Dashboard UID |
| jsonPath | ✅ | string | e.g., "$.panels[*].title" |

### update_dashboard

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| uid | | string | For patching existing |
| dashboard | | object | For creating new |
| operations | | array | Patch operations |
| message | | string | Commit message |
| folderUid | | string | Target folder |
