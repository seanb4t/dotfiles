# Token Efficiency Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce token usage in the Grafana skill through output formatting, compound workflows, and pre-baked schemas.

**Architecture:** Extend `grafana_mcp.py` with output format options and workflow commands. Add YAML output support via PyYAML. Embed tool schemas directly in reference markdown files.

**Tech Stack:** Python 3.11+, httpx, PyYAML, pytest (for testing)

---

## Phase 1: Output Formatting

### Task 1.1: Add PyYAML dependency

**Files:**

- Modify: `grafana/skills/grafana/scripts/grafana_mcp.py:1-6`

**Step 1: Update inline script dependencies**

Change the PEP 723 header to include PyYAML:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "pyyaml"]
# ///
```

**Step 2: Verify dependency loads**

Run: `grafana/skills/grafana/scripts/grafana_mcp.py --list-tools`
Expected: Should work (PyYAML installed on demand by uv)

**Step 3: Commit**

```bash
git add grafana/skills/grafana/scripts/grafana_mcp.py
git commit -m "build(grafana): add pyyaml dependency for yaml output"
```

---

### Task 1.2: Add --format flag

**Files:**

- Modify: `grafana/skills/grafana/scripts/grafana_mcp.py`

**Step 1: Add format argument to argparse**

After the `--describe` argument (around line 193), add:

```python
parser.add_argument(
    "--format",
    choices=["json", "yaml", "compact"],
    default="yaml",
    help="Output format: json (compact), yaml (default), compact (minimal)",
)
```

**Step 2: Add import for yaml at top of file**

After `import json` (line 25), add:

```python
import yaml
```

**Step 3: Create output formatter function**

Before `def main():` (around line 173), add:

```python
def format_output(data: dict[str, Any], fmt: str) -> str:
    """Format output data according to specified format."""
    if fmt == "json":
        return json.dumps(data, separators=(",", ":"))
    elif fmt == "yaml":
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    else:  # compact - will be enhanced per-tool later
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
```

**Step 4: Update main() to use formatter**

Replace all `print(json.dumps(result, indent=2))` calls with `print(format_output(result, args.format))`.

There are 4 locations:

- Line ~214 (list_tools)
- Line ~219 (describe)
- Line ~228 (invalid JSON error)
- Line ~232 (tool call)

**Step 5: Test yaml output**

Run: `grafana/skills/grafana/scripts/grafana_mcp.py --list-tools`
Expected: YAML formatted output (no braces, indented)

Run: `grafana/skills/grafana/scripts/grafana_mcp.py --list-tools --format json`
Expected: Compact single-line JSON

**Step 6: Commit**

```bash
git add grafana/skills/grafana/scripts/grafana_mcp.py
git commit -m "feat(grafana): add --format flag for yaml/json/compact output"
```

---

### Task 1.3: Add --brief flag

**Files:**

- Modify: `grafana/skills/grafana/scripts/grafana_mcp.py`

**Step 1: Add brief argument to argparse**

After the `--format` argument, add:

```python
parser.add_argument(
    "--brief",
    action="store_true",
    help="Return only essential fields (tool-specific filtering)",
)
```

**Step 2: Create brief filter registry**

Before `format_output()`, add:

```python
# Field filters for --brief mode (tool_name -> list of fields to keep)
BRIEF_FILTERS: dict[str, list[str]] = {
    "list_datasources": ["uid", "name", "type"],
    "search_dashboards": ["uid", "title", "folderTitle", "tags"],
    "list_alert_rules": ["uid", "title", "state", "labels"],
    "list_incidents": ["id", "title", "status", "severity"],
    "list_oncall_schedules": ["id", "name", "teamId"],
    "list_contact_points": ["uid", "name", "type"],
}


def apply_brief_filter(data: dict[str, Any], tool_name: str) -> dict[str, Any]:
    """Apply brief filter to reduce output fields."""
    if tool_name not in BRIEF_FILTERS:
        return data

    fields = BRIEF_FILTERS[tool_name]
    result = data.get("result", {})

    # Handle MCP content wrapper
    if "content" in result and isinstance(result["content"], list):
        for item in result["content"]:
            if item.get("type") == "text" and "text" in item:
                try:
                    parsed = json.loads(item["text"])
                    if isinstance(parsed, list):
                        filtered = [{k: v for k, v in obj.items() if k in fields} for obj in parsed]
                        item["text"] = json.dumps(filtered)
                    elif isinstance(parsed, dict) and "items" in parsed:
                        filtered = [{k: v for k, v in obj.items() if k in fields} for obj in parsed["items"]]
                        parsed["items"] = filtered
                        item["text"] = json.dumps(parsed)
                except (json.JSONDecodeError, TypeError):
                    pass

    return data
```

**Step 3: Apply filter in call_tool path**

In `main()`, after `result = client.call_tool(...)`, add:

```python
if args.brief:
    result = apply_brief_filter(result, args.tool)
```

**Step 4: Test brief mode**

Run: `grafana/skills/grafana/scripts/grafana_mcp.py list_datasources '{}' --brief`
Expected: Only uid, name, type fields per datasource

**Step 5: Commit**

```bash
git add grafana/skills/grafana/scripts/grafana_mcp.py
git commit -m "feat(grafana): add --brief flag for reduced output fields"
```

---

### Task 1.4: Flatten wrapper structure and errors to stderr

**Files:**

- Modify: `grafana/skills/grafana/scripts/grafana_mcp.py`

**Step 1: Create unwrap function**

Before `format_output()`, add:

```python
def unwrap_result(data: dict[str, Any]) -> Any:
    """Unwrap MCP result structure to return just the data."""
    if not data.get("success"):
        return data  # Keep error structure

    result = data.get("result", {})

    # Handle MCP content wrapper: {"content": [{"type": "text", "text": "..."}]}
    if "content" in result and isinstance(result["content"], list):
        texts = []
        for item in result["content"]:
            if item.get("type") == "text" and "text" in item:
                try:
                    texts.append(json.loads(item["text"]))
                except json.JSONDecodeError:
                    texts.append(item["text"])

        if len(texts) == 1:
            return texts[0]
        return texts

    return result
```

**Step 2: Update output logic in main()**

Replace the tool call output section with:

```python
result = client.call_tool(args.tool, arguments)
if args.brief:
    result = apply_brief_filter(result, args.tool)

if result.get("success"):
    output = unwrap_result(result)
    print(format_output(output, args.format))
    sys.exit(0)
else:
    print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
    sys.exit(1)
```

**Step 3: Update list_tools output**

```python
if args.list_tools:
    result = client.list_tools()
    if result.get("success"):
        print(format_output(result["tools"], args.format))
        sys.exit(0)
    else:
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
```

**Step 4: Update describe output**

```python
if args.describe:
    result = client.describe_tool(args.describe)
    if result.get("success"):
        print(format_output(result["tool"], args.format))
        sys.exit(0)
    else:
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
```

**Step 5: Test flattened output**

Run: `grafana/skills/grafana/scripts/grafana_mcp.py list_datasources '{}'`
Expected: Direct array of datasources (no success/result wrapper)

Run: `grafana/skills/grafana/scripts/grafana_mcp.py bad_tool '{}' 2>&1`
Expected: "Error: ..." on stderr, exit code 1

**Step 6: Commit**

```bash
git add grafana/skills/grafana/scripts/grafana_mcp.py
git commit -m "feat(grafana): flatten output structure, errors to stderr"
```

---

## Phase 2: Compound Workflows

### Task 2.1: Add workflow infrastructure

**Files:**

- Modify: `grafana/skills/grafana/scripts/grafana_mcp.py`

**Step 1: Add workflow subparser**

After the regular arguments, restructure to use subparsers:

```python
def main():
    parser = argparse.ArgumentParser(
        description="Grafana MCP Gateway - invoke Grafana tools without MCP context overhead",
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("GRAFANA_MCP_URL", DEFAULT_MCP_URL),
        help=f"MCP server URL (default: {DEFAULT_MCP_URL})",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "compact"],
        default="yaml",
        help="Output format (default: yaml)",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Return only essential fields",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Tool operations
    tool_parser = subparsers.add_parser("tool", help="Call an MCP tool")
    tool_parser.add_argument("name", help="Tool name")
    tool_parser.add_argument("arguments", nargs="?", default="{}", help="JSON arguments")

    # List tools
    subparsers.add_parser("list-tools", help="List available MCP tools")

    # Describe tool
    describe_parser = subparsers.add_parser("describe", help="Describe a tool's schema")
    describe_parser.add_argument("name", help="Tool name")

    # Workflows
    investigate_logs = subparsers.add_parser("investigate-logs", help="Find errors in logs")
    investigate_logs.add_argument("params", nargs="?", default="{}", help='{"app":"...","timeRange":"1h"}')

    investigate_metrics = subparsers.add_parser("investigate-metrics", help="Check metric health")
    investigate_metrics.add_argument("params", nargs="?", default="{}", help='{"job":"...","metric":"..."}')

    quick_status = subparsers.add_parser("quick-status", help="System health overview")
    quick_status.add_argument("params", nargs="?", default="{}", help="Optional filters")

    find_dashboard = subparsers.add_parser("find-dashboard", help="Search and summarize dashboard")
    find_dashboard.add_argument("params", nargs="?", default="{}", help='{"query":"..."}')
```

**Step 2: Add backward compatibility for old CLI style**

Before parsing, detect old-style invocation:

```python
def main():
    # Backward compatibility: convert old style to new style
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg == "--list-tools":
            sys.argv = [sys.argv[0], "list-tools"] + sys.argv[2:]
        elif first_arg == "--describe":
            sys.argv = [sys.argv[0], "describe"] + sys.argv[2:]
        elif first_arg.startswith("--"):
            pass  # Regular flag
        elif first_arg not in ["tool", "list-tools", "describe", "investigate-logs",
                                "investigate-metrics", "quick-status", "find-dashboard"]:
            # Old style: tool_name '{args}' -> tool tool_name '{args}'
            sys.argv = [sys.argv[0], "tool"] + sys.argv[1:]

    # ... rest of main
```

**Step 3: Test backward compatibility**

Run: `grafana/skills/grafana/scripts/grafana_mcp.py list_datasources '{}'`
Expected: Works (converted to `tool list_datasources '{}'`)

Run: `grafana/skills/grafana/scripts/grafana_mcp.py list-tools`
Expected: Works (new style)

**Step 4: Commit**

```bash
git add grafana/skills/grafana/scripts/grafana_mcp.py
git commit -m "feat(grafana): add subparser infrastructure for workflows"
```

---

### Task 2.2: Implement investigate-logs workflow

**Files:**

- Modify: `grafana/skills/grafana/scripts/grafana_mcp.py`

**Step 1: Add workflow function**

Before `main()`, add:

```python
def workflow_investigate_logs(client: MCPClient, params: dict[str, Any], fmt: str) -> int:
    """Find errors in logs for a service."""
    app = params.get("app", "")
    time_range = params.get("timeRange", "1h")
    pattern = params.get("pattern", "error")

    if not app:
        print("Error: 'app' parameter is required", file=sys.stderr)
        return 1

    # Step 1: Find Loki datasource
    ds_result = client.call_tool("list_datasources", {"type": "loki"})
    if not ds_result.get("success"):
        print(f"Error finding Loki datasource: {ds_result.get('error')}", file=sys.stderr)
        return 1

    loki_uid = None
    content = ds_result.get("result", {}).get("content", [])
    for item in content:
        if item.get("type") == "text":
            try:
                datasources = json.loads(item["text"])
                if datasources:
                    loki_uid = datasources[0].get("uid")
                    break
            except (json.JSONDecodeError, TypeError, IndexError):
                pass

    if not loki_uid:
        print("Error: No Loki datasource found", file=sys.stderr)
        return 1

    logql = f'{{app="{app}"}}'

    # Step 2: Query stats
    stats_result = client.call_tool("query_loki_stats", {
        "datasourceUid": loki_uid,
        "logql": logql,
    })

    stats = {"streams": 0, "entries": 0, "bytes": 0}
    if stats_result.get("success"):
        content = stats_result.get("result", {}).get("content", [])
        for item in content:
            if item.get("type") == "text":
                try:
                    stats = json.loads(item["text"])
                except (json.JSONDecodeError, TypeError):
                    pass

    # Step 3: Query logs with error pattern
    error_logql = f'{{app="{app}"}} |= "{pattern}"'
    logs_result = client.call_tool("query_loki_logs", {
        "datasourceUid": loki_uid,
        "logql": error_logql,
        "limit": 20,
        "startRfc3339": f"now-{time_range}",
    })

    errors = []
    if logs_result.get("success"):
        content = logs_result.get("result", {}).get("content", [])
        for item in content:
            if item.get("type") == "text":
                try:
                    log_entries = json.loads(item["text"])
                    if isinstance(log_entries, list):
                        errors = [f"{e.get('timestamp', '')} {e.get('line', '')[:100]}"
                                  for e in log_entries[:5]]
                except (json.JSONDecodeError, TypeError):
                    pass

    # Build output
    output = {
        "datasource": loki_uid,
        "timeRange": f"now-{time_range} to now",
        "query": error_logql,
        "stats": stats,
        "errors": {
            "count": len(errors),
            "sample": errors,
        }
    }

    print(format_output(output, fmt))
    return 0
```

**Step 2: Wire up in main()**

In the command dispatch section:

```python
if args.command == "investigate-logs":
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON params: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(workflow_investigate_logs(client, params, args.format))
```

**Step 3: Test workflow**

Run: `grafana/skills/grafana/scripts/grafana_mcp.py investigate-logs '{"app":"nginx","timeRange":"1h"}'`
Expected: Consolidated output with stats and error samples

**Step 4: Commit**

```bash
git add grafana/skills/grafana/scripts/grafana_mcp.py
git commit -m "feat(grafana): add investigate-logs compound workflow"
```

---

### Task 2.3: Implement remaining workflows

**Files:**

- Modify: `grafana/skills/grafana/scripts/grafana_mcp.py`

**Step 1: Add investigate-metrics workflow**

```python
def workflow_investigate_metrics(client: MCPClient, params: dict[str, Any], fmt: str) -> int:
    """Check metric health for a job/service."""
    job = params.get("job", "")
    metric = params.get("metric", "up")
    time_range = params.get("timeRange", "1h")

    # Find Prometheus datasource
    ds_result = client.call_tool("list_datasources", {"type": "prometheus"})
    if not ds_result.get("success"):
        print(f"Error finding Prometheus datasource: {ds_result.get('error')}", file=sys.stderr)
        return 1

    prom_uid = None
    content = ds_result.get("result", {}).get("content", [])
    for item in content:
        if item.get("type") == "text":
            try:
                datasources = json.loads(item["text"])
                if datasources:
                    prom_uid = datasources[0].get("uid")
                    break
            except (json.JSONDecodeError, TypeError, IndexError):
                pass

    if not prom_uid:
        print("Error: No Prometheus datasource found", file=sys.stderr)
        return 1

    # Build query
    if job:
        expr = f'{metric}{{job="{job}"}}'
    else:
        expr = metric

    # Query current value
    query_result = client.call_tool("query_prometheus", {
        "datasourceUid": prom_uid,
        "expr": expr,
        "startTime": f"now-{time_range}",
        "queryType": "instant",
    })

    value = None
    if query_result.get("success"):
        content = query_result.get("result", {}).get("content", [])
        for item in content:
            if item.get("type") == "text":
                try:
                    result = json.loads(item["text"])
                    if result and "value" in result:
                        value = result["value"]
                except (json.JSONDecodeError, TypeError):
                    pass

    output = {
        "datasource": prom_uid,
        "query": expr,
        "timeRange": f"now-{time_range}",
        "result": value if value else "no data",
    }

    print(format_output(output, fmt))
    return 0
```

**Step 2: Add quick-status workflow**

```python
def workflow_quick_status(client: MCPClient, params: dict[str, Any], fmt: str) -> int:
    """Overview of system health."""
    output = {"incidents": {"active": 0}, "alerts": {"firing": []}}

    # Get active incidents
    inc_result = client.call_tool("list_incidents", {"status": "active", "limit": 10})
    if inc_result.get("success"):
        content = inc_result.get("result", {}).get("content", [])
        for item in content:
            if item.get("type") == "text":
                try:
                    incidents = json.loads(item["text"])
                    if isinstance(incidents, list):
                        output["incidents"]["active"] = len(incidents)
                        output["incidents"]["items"] = [
                            {"title": i.get("title"), "severity": i.get("severity")}
                            for i in incidents[:5]
                        ]
                except (json.JSONDecodeError, TypeError):
                    pass

    # Get firing alerts
    alert_result = client.call_tool("list_alert_rules", {"limit": 50})
    if alert_result.get("success"):
        content = alert_result.get("result", {}).get("content", [])
        for item in content:
            if item.get("type") == "text":
                try:
                    alerts = json.loads(item["text"])
                    if isinstance(alerts, list):
                        firing = [a for a in alerts if a.get("state") == "firing"]
                        output["alerts"]["firing"] = [
                            f"{a.get('title')} ({a.get('labels', {}).get('severity', 'unknown')})"
                            for a in firing[:10]
                        ]
                except (json.JSONDecodeError, TypeError):
                    pass

    print(format_output(output, fmt))
    return 0
```

**Step 3: Add find-dashboard workflow**

```python
def workflow_find_dashboard(client: MCPClient, params: dict[str, Any], fmt: str) -> int:
    """Search and summarize a dashboard."""
    query = params.get("query", "")
    if not query:
        print("Error: 'query' parameter is required", file=sys.stderr)
        return 1

    # Search dashboards
    search_result = client.call_tool("search_dashboards", {"query": query})
    if not search_result.get("success"):
        print(f"Error searching dashboards: {search_result.get('error')}", file=sys.stderr)
        return 1

    dashboards = []
    content = search_result.get("result", {}).get("content", [])
    for item in content:
        if item.get("type") == "text":
            try:
                dashboards = json.loads(item["text"])
            except (json.JSONDecodeError, TypeError):
                pass

    if not dashboards:
        print(format_output({"found": 0, "message": "No dashboards found"}, fmt))
        return 0

    # Get summary of top match
    top = dashboards[0]
    summary_result = client.call_tool("get_dashboard_summary", {"uid": top.get("uid")})

    summary = {}
    if summary_result.get("success"):
        content = summary_result.get("result", {}).get("content", [])
        for item in content:
            if item.get("type") == "text":
                try:
                    summary = json.loads(item["text"])
                except (json.JSONDecodeError, TypeError):
                    pass

    output = {
        "found": len(dashboards),
        "top_match": {
            "uid": top.get("uid"),
            "title": top.get("title"),
            "folder": top.get("folderTitle", "General"),
            "panels": summary.get("panelCount", 0),
            "types": summary.get("panelTypes", []),
            "variables": summary.get("variables", []),
            "url": top.get("url", ""),
        }
    }

    print(format_output(output, fmt))
    return 0
```

**Step 4: Wire up remaining workflows in main()**

```python
elif args.command == "investigate-metrics":
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON params: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(workflow_investigate_metrics(client, params, args.format))

elif args.command == "quick-status":
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON params: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(workflow_quick_status(client, params, args.format))

elif args.command == "find-dashboard":
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON params: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(workflow_find_dashboard(client, params, args.format))
```

**Step 5: Test all workflows**

Run: `grafana/skills/grafana/scripts/grafana_mcp.py quick-status '{}'`
Run: `grafana/skills/grafana/scripts/grafana_mcp.py find-dashboard '{"query":"cpu"}'`
Expected: Consolidated YAML output

**Step 6: Commit**

```bash
git add grafana/skills/grafana/scripts/grafana_mcp.py
git commit -m "feat(grafana): add investigate-metrics, quick-status, find-dashboard workflows"
```

---

## Phase 3: Pre-baked Tool Schemas

### Task 3.1: Add schemas to prometheus.md

**Files:**

- Modify: `grafana/skills/grafana/references/prometheus.md`

**Step 1: Add Tool Reference section**

Append to end of file:

```markdown

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
```

**Step 2: Commit**

```bash
git add grafana/skills/grafana/references/prometheus.md
git commit -m "docs(grafana): add tool schemas to prometheus.md"
```

---

### Task 3.2: Add schemas to loki.md

**Files:**

- Modify: `grafana/skills/grafana/references/loki.md`

**Step 1: Add Tool Reference section**

Append to end of file:

```markdown

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
```

**Step 2: Commit**

```bash
git add grafana/skills/grafana/references/loki.md
git commit -m "docs(grafana): add tool schemas to loki.md"
```

---

### Task 3.3: Add schemas to remaining reference files

**Files:**

- Modify: `grafana/skills/grafana/references/dashboards.md`
- Modify: `grafana/skills/grafana/references/alerting.md`
- Modify: `grafana/skills/grafana/references/incidents.md`
- Modify: `grafana/skills/grafana/references/oncall.md`

**Step 1: Add to dashboards.md**

```markdown

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
```

**Step 2: Add to alerting.md**

```markdown

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
```

**Step 3: Add to incidents.md**

```markdown

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
```

**Step 4: Add to oncall.md**

```markdown

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
```

**Step 5: Commit all**

```bash
git add grafana/skills/grafana/references/*.md
git commit -m "docs(grafana): add tool schemas to all reference files"
```

---

## Phase 4: SKILL.md Update

### Task 4.1: Update SKILL.md with new features

**Files:**

- Modify: `grafana/skills/grafana/SKILL.md`

**Step 1: Update Commands section**

Replace the Commands section with:

```markdown
### Commands

```bash
# Discovery
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list-tools
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py describe <tool_name>

# Tool invocation
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py <tool_name> '<json_arguments>'

# Compound workflows (recommended for common tasks)
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py investigate-logs '{"app":"...","timeRange":"1h"}'
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py investigate-metrics '{"job":"...","metric":"..."}'
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py quick-status '{}'
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py find-dashboard '{"query":"..."}'
```
```


```text

### Output Options

```bash
--format yaml    # YAML output (default)
--format json    # Compact JSON
--format compact # Minimal output
--brief          # Essential fields only
```

```text

**Step 2: Add Workflows section after Quick Reference**

```markdown
## Compound Workflows

Use these for common multi-step operations (saves tokens vs individual calls):

### investigate-logs
Find errors in logs for an application:
```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py investigate-logs '{"app":"nginx","timeRange":"1h","pattern":"error"}'
```

### investigate-metrics

Check metric health:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py investigate-metrics '{"job":"api","metric":"http_requests_total"}'
```

### quick-status

System health overview:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py quick-status '{}'
```

### find-dashboard

Search and summarize:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py find-dashboard '{"query":"api latency"}'
```

```text

**Step 3: Commit**

```bash
git add grafana/skills/grafana/SKILL.md
git commit -m "docs(grafana): update SKILL.md with workflows and output options"
```

---

## Phase 5: Version Bump

### Task 5.1: Bump versions to 0.2.0

**Files:**

- Modify: `.claude-plugin/marketplace.json`
- Modify: `grafana/plugin.json`

**Step 1: Update marketplace.json**

Change version from "0.1.0" to "0.2.0"

**Step 2: Update plugin.json**

Change version from "0.1.0" to "0.2.0"

**Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json grafana/plugin.json
git commit -m "chore: bump version to 0.2.0

New features:
- Output format options (--format yaml|json|compact, --brief)
- Compound workflows (investigate-logs, investigate-metrics, quick-status, find-dashboard)
- Pre-baked tool schemas in reference files"
```

**Step 4: Push all changes**

```bash
git push origin main
```

---

## Verification

After implementation, verify:

1. `grafana_mcp.py list-tools` outputs YAML by default
2. `grafana_mcp.py list_datasources '{}' --brief` shows only uid/name/type
3. `grafana_mcp.py investigate-logs '{"app":"test"}'` runs compound workflow
4. `grafana_mcp.py quick-status '{}'` shows incidents and alerts
5. Reference files contain tool schema tables
6. Version is 0.2.0 in both manifest files
