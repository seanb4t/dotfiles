# Terraform Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a skill that wraps the HashiCorp Terraform MCP server to provide streamlined TFC operations and provider documentation lookup.

**Architecture:** Single Python gateway script using uv, spawning Docker container for Terraform MCP server via stdio JSON-RPC. Session management keeps container alive to avoid startup overhead. Hybrid client uses MCP for structured ops, direct HCP API for log streaming.

**Tech Stack:** Python 3.11+, uv (inline dependencies), httpx, Docker, JSON-RPC 2.0

---

## Task 1: Create Directory Structure

**Files:**

- Create: `fzymgc-house/skills/terraform/SKILL.md`
- Create: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`
- Create: `fzymgc-house/skills/terraform/references/workspaces.md`
- Create: `fzymgc-house/skills/terraform/references/runs.md`
- Create: `fzymgc-house/skills/terraform/references/providers.md`

**Step 1: Create directory structure**

```bash
mkdir -p fzymgc-house/skills/terraform/scripts
mkdir -p fzymgc-house/skills/terraform/references
```

**Step 2: Create stub SKILL.md**

Create `fzymgc-house/skills/terraform/SKILL.md`:

```markdown
---
name: terraform
description: |
  Terraform Cloud operations and registry documentation lookup.
  Watch runs, view plan/apply logs, check workspace status, look up provider docs.
  Invokes Terraform MCP server on-demand without loading tool definitions into context.
---

# Terraform Operations

> **Under Construction** - Implementation in progress.
```

**Step 3: Create empty reference files**

Create `fzymgc-house/skills/terraform/references/workspaces.md`:

```markdown
# Workspace Operations Reference

> Placeholder - detailed workspace operations documentation.
```

Create `fzymgc-house/skills/terraform/references/runs.md`:

```markdown
# Run Operations Reference

> Placeholder - detailed run operations documentation.
```

Create `fzymgc-house/skills/terraform/references/providers.md`:

```markdown
# Provider Documentation Reference

> Placeholder - detailed provider lookup documentation.
```

**Step 4: Commit directory structure**

```bash
git add fzymgc-house/skills/terraform/
git commit -m "feat(terraform): scaffold terraform skill directory structure"
```

---

## Task 2: Implement MCP Stdio Client

**Files:**

- Create: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`

**Step 1: Create gateway script with MCP client**

Create `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "pyyaml"]
# ///
"""
Terraform MCP Gateway Script

Invokes Terraform MCP server tools without requiring MCP server configuration.
Reduces context overhead by not loading all MCP tool definitions.

Usage:
    terraform_mcp.py list-tools                    # List available tools
    terraform_mcp.py describe <tool>               # Describe a tool's schema
    terraform_mcp.py tool <name> '<json_args>'     # Call a raw tool

Environment Variables:
    TFE_TOKEN    - HCP Terraform API token (required)
    TFE_ORG      - Default organization name (required)
    TFE_ADDRESS  - TFC/TFE URL (default: https://app.terraform.io)
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

# Configuration
DEFAULT_TFE_ADDRESS = "https://app.terraform.io"
DOCKER_IMAGE = "hashicorp/terraform-mcp-server:0.3.3"
SESSION_DIR = Path.home() / ".cache" / "terraform-mcp"
SESSION_TIMEOUT = 300  # 5 minutes
POLL_INTERVAL = 5  # seconds


class MCPStdioClient:
    """MCP client communicating via stdio with Docker container."""

    def __init__(self, proc: subprocess.Popen):
        self.proc = proc
        self.request_id = 0
        self._initialized = False

    def _send(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send JSON-RPC request and receive response."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }

        try:
            line = json.dumps(request) + "\n"
            self.proc.stdin.write(line.encode())
            self.proc.stdin.flush()

            response_line = self.proc.stdout.readline()
            if not response_line:
                return {"error": {"message": "No response from server"}}

            return json.loads(response_line)
        except (BrokenPipeError, json.JSONDecodeError) as e:
            return {"error": {"message": str(e)}}

    def initialize(self) -> dict[str, Any]:
        """Initialize the MCP session."""
        if self._initialized:
            return {"success": True}

        result = self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "terraform-mcp-gateway", "version": "1.0.0"},
        })

        if "error" not in result:
            self._initialized = True
            # Send initialized notification
            self._send("notifications/initialized", {})

        return result

    def list_tools(self) -> dict[str, Any]:
        """List all available tools."""
        self.initialize()
        result = self._send("tools/list")

        if "error" in result:
            return {"success": False, "error": result["error"].get("message", str(result["error"]))}

        if "result" in result and "tools" in result["result"]:
            tool_names = [t["name"] for t in result["result"]["tools"]]
            return {"success": True, "tools": sorted(tool_names)}

        return {"success": False, "error": f"Unexpected response: {result}"}

    def describe_tool(self, tool_name: str) -> dict[str, Any]:
        """Get schema for a specific tool."""
        self.initialize()
        result = self._send("tools/list")

        if "error" in result:
            return {"success": False, "error": result["error"].get("message", str(result["error"]))}

        if "result" in result and "tools" in result["result"]:
            for tool in result["result"]["tools"]:
                if tool["name"] == tool_name:
                    return {
                        "success": True,
                        "tool": {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "inputSchema": tool.get("inputSchema", {}),
                        },
                    }

            all_tools = [t["name"] for t in result["result"]["tools"]]
            similar = [t for t in all_tools if tool_name.lower() in t.lower()]
            msg = f"Tool '{tool_name}' not found."
            if similar:
                msg += f" Similar: {', '.join(similar[:5])}"
            return {"success": False, "error": msg}

        return {"success": False, "error": f"Unexpected response: {result}"}

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool with arguments."""
        self.initialize()
        result = self._send("tools/call", {"name": tool_name, "arguments": arguments})

        if "error" in result:
            return {"success": False, "error": result["error"].get("message", str(result["error"]))}

        if "result" in result:
            return {"success": True, "result": result["result"]}

        return {"success": False, "error": f"Unexpected response: {result}"}

    def close(self):
        """Terminate the MCP server process."""
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


class SessionManager:
    """Manage Docker container session for MCP server."""

    def __init__(self):
        self.session_dir = SESSION_DIR
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file = self.session_dir / "server.pid"
        self.proc: subprocess.Popen | None = None

    def _get_env(self) -> dict[str, str]:
        """Get environment variables for Docker container."""
        token = os.environ.get("TFE_TOKEN")
        if not token:
            raise EnvironmentError("TFE_TOKEN environment variable is required")

        address = os.environ.get("TFE_ADDRESS", DEFAULT_TFE_ADDRESS)

        return {
            "TFE_TOKEN": token,
            "TFE_ADDRESS": address,
        }

    def _spawn_container(self) -> subprocess.Popen:
        """Spawn a new Docker container."""
        env = self._get_env()

        cmd = [
            "docker", "run", "-i", "--rm",
            "-e", f"TFE_TOKEN={env['TFE_TOKEN']}",
            "-e", f"TFE_ADDRESS={env['TFE_ADDRESS']}",
            DOCKER_IMAGE,
        ]

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Save PID for session reuse (future enhancement)
        self.pid_file.write_text(str(proc.pid))

        return proc

    def get_client(self) -> MCPStdioClient:
        """Get or create MCP client."""
        # For now, always spawn fresh container
        # Session reuse can be added later
        self.proc = self._spawn_container()
        return MCPStdioClient(self.proc)

    def cleanup(self):
        """Clean up resources."""
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

        if self.pid_file.exists():
            self.pid_file.unlink()


def unwrap_result(data: dict[str, Any]) -> Any:
    """Unwrap MCP result structure to return just the data."""
    if not data.get("success"):
        return data

    result = data.get("result", {})

    # Handle MCP content wrapper: {"content": [{"type": "text", "text": "..."}]}
    if "content" in result and isinstance(result["content"], list):
        texts = []
        for item in result["content"]:
            if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                try:
                    texts.append(json.loads(item["text"]))
                except json.JSONDecodeError:
                    texts.append(item["text"])

        if len(texts) == 1:
            return texts[0]
        return texts

    return result


def format_output(data: Any, fmt: str) -> str:
    """Format output according to specified format."""
    if fmt == "json":
        return json.dumps(data, separators=(",", ":"))
    elif fmt == "yaml":
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    else:  # compact
        return yaml.dump(data, default_flow_style=False, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(
        description="Terraform MCP Gateway - invoke Terraform tools without MCP context overhead",
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

    # list-tools
    subparsers.add_parser("list-tools", help="List available MCP tools")

    # describe
    describe_parser = subparsers.add_parser("describe", help="Describe a tool's schema")
    describe_parser.add_argument("name", help="Tool name")

    # tool (raw tool call)
    tool_parser = subparsers.add_parser("tool", help="Call an MCP tool directly")
    tool_parser.add_argument("name", help="Tool name")
    tool_parser.add_argument("arguments", nargs="?", default="{}", help="JSON arguments")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    session = SessionManager()

    try:
        client = session.get_client()

        if args.command == "list-tools":
            result = client.list_tools()
            if result.get("success"):
                print(format_output(result["tools"], args.format))
                sys.exit(0)
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.command == "describe":
            result = client.describe_tool(args.name)
            if result.get("success"):
                print(format_output(result["tool"], args.format))
                sys.exit(0)
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.command == "tool":
            try:
                arguments = json.loads(args.arguments)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON arguments: {e}", file=sys.stderr)
                sys.exit(1)

            result = client.call_tool(args.name, arguments)
            output = unwrap_result(result)

            if result.get("success"):
                print(format_output(output, args.format))
                sys.exit(0)
            else:
                print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)

    except EnvironmentError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.cleanup()


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

```bash
chmod +x fzymgc-house/skills/terraform/scripts/terraform_mcp.py
```

**Step 3: Test basic functionality (requires Docker and TFE_TOKEN)**

```bash
# Verify script runs
TFE_TOKEN=test TFE_ORG=test fzymgc-house/skills/terraform/scripts/terraform_mcp.py --help

# If you have valid credentials, test list-tools:
# fzymgc-house/skills/terraform/scripts/terraform_mcp.py list-tools
```

Expected: Help output displays, no Python errors.

**Step 4: Commit MCP client**

```bash
git add fzymgc-house/skills/terraform/scripts/terraform_mcp.py
git commit -m "feat(terraform): implement MCP stdio client and session manager

- MCPStdioClient: JSON-RPC 2.0 over stdio to Docker container
- SessionManager: spawns/manages Docker container lifecycle
- Basic commands: list-tools, describe, tool (raw call)
- Output formatting: yaml, json, compact"
```

---

## Task 3: Add Direct HCP API Client

**Files:**

- Modify: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`

**Step 1: Add HCPTerraformClient class**

Add after the `SessionManager` class in `terraform_mcp.py`:

```python
class HCPTerraformClient:
    """Direct HCP Terraform API client for operations not exposed via MCP."""

    def __init__(self, token: str, address: str = DEFAULT_TFE_ADDRESS):
        import httpx
        self.client = httpx.Client(
            base_url=address.rstrip("/"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/vnd.api+json",
            },
            timeout=30.0,
        )

    def get_plan_logs(self, plan_id: str) -> str:
        """Fetch plan logs from HCP Terraform API."""
        try:
            # First get the plan to find the log URL
            resp = self.client.get(f"/api/v2/plans/{plan_id}")
            resp.raise_for_status()
            plan_data = resp.json()

            log_url = plan_data.get("data", {}).get("attributes", {}).get("log-read-url")
            if not log_url:
                return "[No log URL available]"

            # Fetch the actual logs
            log_resp = httpx.get(log_url, timeout=30.0)
            log_resp.raise_for_status()
            return log_resp.text
        except Exception as e:
            return f"[Error fetching plan logs: {e}]"

    def get_apply_logs(self, apply_id: str) -> str:
        """Fetch apply logs from HCP Terraform API."""
        try:
            resp = self.client.get(f"/api/v2/applies/{apply_id}")
            resp.raise_for_status()
            apply_data = resp.json()

            log_url = apply_data.get("data", {}).get("attributes", {}).get("log-read-url")
            if not log_url:
                return "[No log URL available]"

            log_resp = httpx.get(log_url, timeout=30.0)
            log_resp.raise_for_status()
            return log_resp.text
        except Exception as e:
            return f"[Error fetching apply logs: {e}]"

    def get_run(self, run_id: str) -> dict[str, Any]:
        """Get run details including plan/apply IDs."""
        try:
            resp = self.client.get(f"/api/v2/runs/{run_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def close(self):
        """Close the HTTP client."""
        self.client.close()
```

**Step 2: Commit HCP API client**

```bash
git add fzymgc-house/skills/terraform/scripts/terraform_mcp.py
git commit -m "feat(terraform): add direct HCP Terraform API client

- HCPTerraformClient for operations not exposed via MCP
- get_plan_logs/get_apply_logs for streaming log output
- get_run for detailed run info with plan/apply IDs"
```

---

## Task 4: Implement workspace-status Workflow

**Files:**

- Modify: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`

**Step 1: Add workspace-status workflow function**

Add before `main()`:

```python
def get_default_org() -> str:
    """Get default organization from environment."""
    org = os.environ.get("TFE_ORG")
    if not org:
        raise EnvironmentError("TFE_ORG environment variable is required")
    return org


def workflow_workspace_status(client: MCPStdioClient, args: argparse.Namespace, fmt: str) -> int:
    """Show workspace status overview."""
    org = get_default_org()
    workspace_name = args.workspace if hasattr(args, "workspace") and args.workspace else None

    if workspace_name:
        # Single workspace detail
        result = client.call_tool("get_workspace_details", {
            "terraform_org_name": org,
            "workspace_name": workspace_name,
        })

        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)

        # Extract key fields
        output = {
            "workspace": workspace_name,
            "organization": org,
            "id": data.get("id", ""),
            "terraform_version": data.get("attributes", {}).get("terraform-version", ""),
            "execution_mode": data.get("attributes", {}).get("execution-mode", ""),
            "auto_apply": data.get("attributes", {}).get("auto-apply", False),
            "working_directory": data.get("attributes", {}).get("working-directory", ""),
            "vcs_repo": data.get("attributes", {}).get("vcs-repo", {}),
            "updated_at": data.get("attributes", {}).get("updated-at", ""),
        }

        print(format_output(output, fmt))
        return 0

    else:
        # List all workspaces
        result = client.call_tool("list_workspaces", {
            "terraform_org_name": org,
        })

        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)

        # Format as brief list
        workspaces = []
        items = data if isinstance(data, list) else data.get("items", [])
        for ws in items:
            attrs = ws.get("attributes", {}) if isinstance(ws, dict) else {}
            workspaces.append({
                "name": attrs.get("name", ws.get("name", "")),
                "id": ws.get("id", ""),
                "terraform_version": attrs.get("terraform-version", ""),
                "updated_at": attrs.get("updated-at", ""),
            })

        output = {
            "organization": org,
            "count": len(workspaces),
            "workspaces": workspaces,
        }

        print(format_output(output, fmt))
        return 0
```

**Step 2: Add subparser for workspace-status**

In `main()`, add after the `tool` subparser:

```python
    # workspace-status
    ws_parser = subparsers.add_parser("workspace-status", help="Show workspace status")
    ws_parser.add_argument("workspace", nargs="?", help="Workspace name (optional, lists all if omitted)")
```

**Step 3: Add handler in main()**

In the command handling section, add:

```python
        elif args.command == "workspace-status":
            sys.exit(workflow_workspace_status(client, args, args.format))
```

**Step 4: Test workspace-status**

```bash
# With valid credentials:
# fzymgc-house/skills/terraform/scripts/terraform_mcp.py workspace-status
# fzymgc-house/skills/terraform/scripts/terraform_mcp.py workspace-status my-workspace
```

**Step 5: Commit workspace-status**

```bash
git add fzymgc-house/skills/terraform/scripts/terraform_mcp.py
git commit -m "feat(terraform): add workspace-status workflow

- List all workspaces in organization
- Show detailed info for single workspace
- Extracts key fields: terraform_version, execution_mode, vcs_repo"
```

---

## Task 5: Implement list-runs Workflow

**Files:**

- Modify: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`

**Step 1: Add list-runs workflow function**

Add after `workflow_workspace_status`:

```python
def workflow_list_runs(client: MCPStdioClient, args: argparse.Namespace, fmt: str) -> int:
    """List recent runs for a workspace."""
    org = get_default_org()
    workspace = args.workspace
    limit = args.limit if hasattr(args, "limit") else 10
    status_filter = args.status if hasattr(args, "status") else None

    params: dict[str, Any] = {
        "terraform_org_name": org,
        "workspace_name": workspace,
        "pageSize": limit,
    }

    if status_filter:
        params["status"] = [status_filter]

    result = client.call_tool("list_runs", params)

    if not result.get("success"):
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return 1

    data = unwrap_result(result)

    runs = []
    items = data if isinstance(data, list) else data.get("items", [])
    for run in items:
        attrs = run.get("attributes", {}) if isinstance(run, dict) else {}
        runs.append({
            "id": run.get("id", ""),
            "status": attrs.get("status", ""),
            "message": attrs.get("message", "")[:80] if attrs.get("message") else "",
            "created_at": attrs.get("created-at", ""),
            "plan_only": attrs.get("plan-only", False),
            "is_destroy": attrs.get("is-destroy", False),
        })

    output = {
        "workspace": workspace,
        "organization": org,
        "count": len(runs),
        "runs": runs,
    }

    print(format_output(output, fmt))
    return 0
```

**Step 2: Add subparser for list-runs**

```python
    # list-runs
    runs_parser = subparsers.add_parser("list-runs", help="List recent runs for a workspace")
    runs_parser.add_argument("workspace", help="Workspace name")
    runs_parser.add_argument("--limit", type=int, default=10, help="Number of runs (default: 10)")
    runs_parser.add_argument("--status", help="Filter by status (e.g., applied, errored, planning)")
```

**Step 3: Add handler**

```python
        elif args.command == "list-runs":
            sys.exit(workflow_list_runs(client, args, args.format))
```

**Step 4: Commit list-runs**

```bash
git add fzymgc-house/skills/terraform/scripts/terraform_mcp.py
git commit -m "feat(terraform): add list-runs workflow

- List recent runs for workspace with pagination
- Filter by status (applied, errored, planning, etc.)
- Shows run ID, status, message, timestamps"
```

---

## Task 6: Implement watch-run Workflow

**Files:**

- Modify: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`

**Step 1: Add watch-run workflow function**

Add after `workflow_list_runs`:

```python
def workflow_watch_run(
    client: MCPStdioClient,
    hcp_client: HCPTerraformClient,
    args: argparse.Namespace,
    fmt: str,
) -> int:
    """Watch a run's progress with live updates."""
    org = get_default_org()
    run_id = args.run_id if hasattr(args, "run_id") and args.run_id else None
    workspace = args.workspace if hasattr(args, "workspace") and args.workspace else None
    show_logs = args.logs if hasattr(args, "logs") else False
    poll_interval = args.interval if hasattr(args, "interval") else POLL_INTERVAL

    # If workspace provided, get latest run
    if not run_id and workspace:
        result = client.call_tool("list_runs", {
            "terraform_org_name": org,
            "workspace_name": workspace,
            "pageSize": 1,
        })
        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            print(f"No runs found for workspace '{workspace}'", file=sys.stderr)
            return 1
        run_id = items[0].get("id")

    if not run_id:
        print("Error: Either --run-id or --workspace is required", file=sys.stderr)
        return 1

    terminal_states = {
        "applied", "errored", "discarded", "canceled", "force_canceled",
        "planned_and_finished", "policy_soft_failed",
    }

    print(f"Watching run: {run_id}", file=sys.stderr)
    print(f"Poll interval: {poll_interval}s", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    last_status = None

    while True:
        result = client.call_tool("get_run_details", {"run_id": run_id})

        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)
        attrs = data.get("attributes", {}) if isinstance(data, dict) else {}
        status = attrs.get("status", "unknown")

        # Print status update if changed
        if status != last_status:
            timestamp = time.strftime("%H:%M:%S")
            plan_summary = ""

            # Try to get plan/apply counts
            if "status-timestamps" in attrs:
                timestamps = attrs["status-timestamps"]
                if timestamps.get("planned-at"):
                    plan_summary = f" | Plan: +{attrs.get('resource-additions', 0)} ~{attrs.get('resource-changes', 0)} -{attrs.get('resource-destructions', 0)}"

            print(f"[{timestamp}] Status: {status}{plan_summary}", file=sys.stderr)
            last_status = status

        # Check for terminal state
        if status in terminal_states:
            print("-" * 50, file=sys.stderr)

            # Get and display logs if requested
            if show_logs:
                # Get plan ID from relationships
                relationships = data.get("relationships", {})
                plan_rel = relationships.get("plan", {}).get("data", {})
                apply_rel = relationships.get("apply", {}).get("data", {})

                if plan_rel.get("id"):
                    print("\n=== Plan Output ===", file=sys.stderr)
                    logs = hcp_client.get_plan_logs(plan_rel["id"])
                    print(logs)

                if apply_rel.get("id") and status == "applied":
                    print("\n=== Apply Output ===", file=sys.stderr)
                    logs = hcp_client.get_apply_logs(apply_rel["id"])
                    print(logs)

            # Final output
            output = {
                "run_id": run_id,
                "status": status,
                "message": attrs.get("message", ""),
                "resource_additions": attrs.get("resource-additions", 0),
                "resource_changes": attrs.get("resource-changes", 0),
                "resource_destructions": attrs.get("resource-destructions", 0),
            }

            if fmt != "compact":
                print(format_output(output, fmt))

            return 0 if status == "applied" else 1

        time.sleep(poll_interval)
```

**Step 2: Update SessionManager and main() to support HCP client**

Update `main()` to create HCP client:

```python
    # After getting MCP client, also create HCP client
    hcp_client = None
    token = os.environ.get("TFE_TOKEN")
    address = os.environ.get("TFE_ADDRESS", DEFAULT_TFE_ADDRESS)
    if token:
        hcp_client = HCPTerraformClient(token, address)
```

And in the finally block:

```python
    finally:
        session.cleanup()
        if hcp_client:
            hcp_client.close()
```

**Step 3: Add subparser for watch-run**

```python
    # watch-run
    watch_parser = subparsers.add_parser("watch-run", help="Watch a run's progress")
    watch_parser.add_argument("run_id", nargs="?", help="Run ID to watch")
    watch_parser.add_argument("--workspace", "-w", help="Watch latest run for workspace")
    watch_parser.add_argument("--logs", "-l", action="store_true", help="Show plan/apply logs when complete")
    watch_parser.add_argument("--interval", "-i", type=int, default=5, help="Poll interval in seconds (default: 5)")
```

**Step 4: Add handler**

```python
        elif args.command == "watch-run":
            if not hcp_client:
                print("Error: TFE_TOKEN required for watch-run", file=sys.stderr)
                sys.exit(1)
            sys.exit(workflow_watch_run(client, hcp_client, args, args.format))
```

**Step 5: Commit watch-run**

```bash
git add fzymgc-house/skills/terraform/scripts/terraform_mcp.py
git commit -m "feat(terraform): add watch-run workflow

- Poll run status with live updates
- Watch by run ID or latest run for workspace
- Optional plan/apply log streaming via HCP API
- Configurable poll interval
- Returns exit code 0 for applied, 1 for failure"
```

---

## Task 7: Implement run-outputs Workflow

**Files:**

- Modify: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`

**Step 1: Add run-outputs workflow function**

```python
def workflow_run_outputs(client: MCPStdioClient, args: argparse.Namespace, fmt: str) -> int:
    """View terraform outputs from a run."""
    org = get_default_org()
    run_id = args.run_id if hasattr(args, "run_id") and args.run_id else None
    workspace = args.workspace if hasattr(args, "workspace") and args.workspace else None

    # If workspace provided, get latest successful run
    if not run_id and workspace:
        result = client.call_tool("list_runs", {
            "terraform_org_name": org,
            "workspace_name": workspace,
            "pageSize": 10,
            "status": ["applied"],
        })
        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            print(f"No successful runs found for workspace '{workspace}'", file=sys.stderr)
            return 1
        run_id = items[0].get("id")

    if not run_id:
        print("Error: Either run_id or --workspace is required", file=sys.stderr)
        return 1

    # Get run details to find state version
    result = client.call_tool("get_run_details", {"run_id": run_id})

    if not result.get("success"):
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return 1

    data = unwrap_result(result)

    # Extract outputs from run if available
    # Note: Outputs may be in state-versions relationship
    outputs = data.get("outputs", {})

    if not outputs:
        # Try to get from attributes
        attrs = data.get("attributes", {}) if isinstance(data, dict) else {}
        outputs = attrs.get("outputs", {})

    if not outputs:
        print(f"No outputs found for run {run_id}", file=sys.stderr)
        print("Note: Outputs may only be available after terraform apply", file=sys.stderr)
        return 1

    output = {
        "run_id": run_id,
        "outputs": outputs,
    }

    print(format_output(output, fmt))
    return 0
```

**Step 2: Add subparser**

```python
    # run-outputs
    outputs_parser = subparsers.add_parser("run-outputs", help="View terraform outputs from a run")
    outputs_parser.add_argument("run_id", nargs="?", help="Run ID")
    outputs_parser.add_argument("--workspace", "-w", help="Get outputs from latest successful run")
```

**Step 3: Add handler**

```python
        elif args.command == "run-outputs":
            sys.exit(workflow_run_outputs(client, args, args.format))
```

**Step 4: Commit run-outputs**

```bash
git add fzymgc-house/skills/terraform/scripts/terraform_mcp.py
git commit -m "feat(terraform): add run-outputs workflow

- View terraform outputs from specific run
- Or latest successful run for workspace"
```

---

## Task 8: Implement provider-docs Workflow

**Files:**

- Modify: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`

**Step 1: Add provider-docs workflow function**

```python
def workflow_provider_docs(client: MCPStdioClient, args: argparse.Namespace, fmt: str) -> int:
    """Look up provider documentation."""
    provider = args.provider
    resource = args.resource if hasattr(args, "resource") and args.resource else None
    data_source = args.data_source if hasattr(args, "data_source") and args.data_source else None
    list_resources = args.list_resources if hasattr(args, "list_resources") else False

    # Determine namespace (default to hashicorp for common providers)
    namespace = args.namespace if hasattr(args, "namespace") and args.namespace else "hashicorp"

    # Common provider namespaces
    provider_namespaces = {
        "aws": "hashicorp",
        "azurerm": "hashicorp",
        "google": "hashicorp",
        "kubernetes": "hashicorp",
        "helm": "hashicorp",
        "vault": "hashicorp",
        "cloudflare": "cloudflare",
        "datadog": "DataDog",
        "github": "integrations",
    }

    if provider in provider_namespaces:
        namespace = provider_namespaces[provider]

    # Determine document type
    if list_resources:
        doc_type = "resources"
        service_slug = provider
    elif resource:
        doc_type = "resources"
        service_slug = resource
    elif data_source:
        doc_type = "data-sources"
        service_slug = data_source
    else:
        doc_type = "overview"
        service_slug = provider

    # Search for provider docs
    result = client.call_tool("search_providers", {
        "provider_name": provider,
        "provider_namespace": namespace,
        "service_slug": service_slug,
        "provider_document_type": doc_type,
    })

    if not result.get("success"):
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return 1

    data = unwrap_result(result)

    # If listing resources, just show the search results
    if list_resources:
        items = data if isinstance(data, list) else [data]
        resources = [{"title": item.get("title", ""), "id": item.get("id", "")} for item in items]
        output = {
            "provider": provider,
            "namespace": namespace,
            "resources": resources,
        }
        print(format_output(output, fmt))
        return 0

    # Get the doc ID from search results
    doc_id = None
    if isinstance(data, list) and data:
        doc_id = data[0].get("id")
    elif isinstance(data, dict):
        doc_id = data.get("id")

    if not doc_id:
        print(f"No documentation found for {provider}/{service_slug}", file=sys.stderr)
        return 1

    # Fetch full documentation
    detail_result = client.call_tool("get_provider_details", {
        "provider_doc_id": str(doc_id),
    })

    if not detail_result.get("success"):
        print(f"Error: {detail_result.get('error')}", file=sys.stderr)
        return 1

    doc_data = unwrap_result(detail_result)

    # Output the documentation
    if fmt == "yaml":
        # For YAML, structure the output
        output = {
            "provider": provider,
            "namespace": namespace,
            "type": doc_type,
            "content": doc_data if isinstance(doc_data, str) else doc_data.get("content", doc_data),
        }
        print(format_output(output, fmt))
    else:
        # For other formats, just print the content
        content = doc_data if isinstance(doc_data, str) else doc_data.get("content", str(doc_data))
        print(content)

    return 0
```

**Step 2: Add subparser**

```python
    # provider-docs
    provider_parser = subparsers.add_parser("provider-docs", help="Look up provider documentation")
    provider_parser.add_argument("provider", help="Provider name (e.g., aws, azurerm, google)")
    provider_parser.add_argument("--namespace", help="Provider namespace (default: auto-detected)")
    provider_parser.add_argument("--resource", "-r", help="Resource name (e.g., lambda_function)")
    provider_parser.add_argument("--data-source", "-d", help="Data source name")
    provider_parser.add_argument("--list-resources", "-l", action="store_true", help="List available resources")
```

**Step 3: Add handler**

```python
        elif args.command == "provider-docs":
            sys.exit(workflow_provider_docs(client, args, args.format))
```

**Step 4: Commit provider-docs**

```bash
git add fzymgc-house/skills/terraform/scripts/terraform_mcp.py
git commit -m "feat(terraform): add provider-docs workflow

- Look up provider overview, resources, data sources
- Auto-detect namespace for common providers
- List available resources with --list-resources"
```

---

## Task 9: Implement list-providers Workflow

**Files:**

- Modify: `fzymgc-house/skills/terraform/scripts/terraform_mcp.py`

**Step 1: Add list-providers workflow function**

```python
def workflow_list_providers(client: MCPStdioClient, args: argparse.Namespace, fmt: str) -> int:
    """List/search available providers."""
    search = args.search if hasattr(args, "search") and args.search else ""
    namespace = args.namespace if hasattr(args, "namespace") and args.namespace else "hashicorp"

    # Use search_providers with overview type to list
    result = client.call_tool("search_providers", {
        "provider_name": search if search else "aws",  # Default search term
        "provider_namespace": namespace,
        "service_slug": search if search else "aws",
        "provider_document_type": "overview",
    })

    if not result.get("success"):
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return 1

    data = unwrap_result(result)

    # Format as list
    items = data if isinstance(data, list) else [data]
    providers = []
    for item in items:
        providers.append({
            "name": item.get("title", ""),
            "id": item.get("id", ""),
            "category": item.get("category", ""),
        })

    output = {
        "search": search,
        "namespace": namespace,
        "count": len(providers),
        "providers": providers,
    }

    print(format_output(output, fmt))
    return 0
```

**Step 2: Add subparser**

```python
    # list-providers
    list_prov_parser = subparsers.add_parser("list-providers", help="List/search providers")
    list_prov_parser.add_argument("--search", "-s", help="Search term")
    list_prov_parser.add_argument("--namespace", "-n", default="hashicorp", help="Provider namespace")
```

**Step 3: Add handler**

```python
        elif args.command == "list-providers":
            sys.exit(workflow_list_providers(client, args, args.format))
```

**Step 4: Commit list-providers**

```bash
git add fzymgc-house/skills/terraform/scripts/terraform_mcp.py
git commit -m "feat(terraform): add list-providers workflow

- Search providers by name
- Filter by namespace"
```

---

## Task 10: Write Complete SKILL.md

**Files:**

- Modify: `fzymgc-house/skills/terraform/SKILL.md`

**Step 1: Write full skill documentation**

Replace `fzymgc-house/skills/terraform/SKILL.md` with:

```markdown
---
name: terraform
description: |
  Terraform Cloud operations and registry documentation lookup.
  Watch runs, view plan/apply logs, check workspace status, look up provider docs.
  Invokes Terraform MCP server on-demand without loading tool definitions into context.
---

# Terraform Operations

## Gateway Script

All operations MUST use the gateway script at `${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py`.

### Configuration

The following environment variables MUST be set:

- `TFE_TOKEN` - HCP Terraform API token
- `TFE_ORG` - Default organization name

The following environment variable MAY be set:

- `TFE_ADDRESS` - TFC/TFE URL (default: <https://app.terraform.io>)

## Quick Reference

| Task | Command |
|------|---------|
| Watch a run | `watch-run <run-id>` |
| Watch latest run | `watch-run --workspace <name>` |
| View run outputs | `run-outputs --workspace <name>` |
| Workspace status | `workspace-status [name]` |
| List runs | `list-runs <workspace>` |
| Provider docs | `provider-docs aws --resource lambda_function` |
| List providers | `list-providers --search cloud` |

## TFC Operations

### watch-run

Monitor a run's progress with live status updates.

```bash
# Watch specific run
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py watch-run run-abc123

# Watch latest run for workspace
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py watch-run --workspace my-workspace

# Include plan/apply logs when complete
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py watch-run --workspace my-workspace --logs
```
```


```text

Options:

- `--workspace`, `-w` - Watch latest run for workspace
- `--logs`, `-l` - Show plan/apply logs when run completes
- `--interval`, `-i` - Poll interval in seconds (default: 5)

The command MUST:

- Poll status at regular intervals
- Display status changes with timestamps
- Show plan summary (resource additions/changes/destructions)
- Exit with code 0 for applied, 1 for failure states

### workspace-status

Show workspace overview or detailed info.

```bash
# List all workspaces
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py workspace-status

# Single workspace detail
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py workspace-status my-workspace
```

### list-runs

List recent runs for a workspace.

```bash
# Recent runs
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py list-runs my-workspace

# With limit
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py list-runs my-workspace --limit 20

# Filter by status
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py list-runs my-workspace --status errored
```

### run-outputs

View terraform outputs from a run.

```bash
# From specific run
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py run-outputs run-abc123

# From latest successful run
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py run-outputs --workspace my-workspace
```

## Documentation Lookup

### provider-docs

Look up provider resource documentation.

```bash
# Provider overview
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py provider-docs aws

# Specific resource
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py provider-docs aws --resource lambda_function

# Data source
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py provider-docs aws --data-source ami

# List available resources
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py provider-docs aws --list-resources
```

### list-providers

Search for providers.

```bash
# Search
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py list-providers --search cloud

# By namespace
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py list-providers --namespace cloudflare
```

## Output Options

```bash
--format yaml    # YAML output (default)
--format json    # Compact JSON
--format compact # Minimal output
```

## Tool Discovery

When unsure about MCP tool parameters:

```bash
# List all available tools
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py list-tools

# Get tool schema
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py describe <tool_name>
```

## Best Practices

- SHOULD use `watch-run --workspace <name>` rather than manually finding run IDs
- SHOULD use `workspace-status` to get an overview before investigating runs
- MUST NOT use raw MCP tools directly when a workflow exists
- SHOULD use `--logs` with `watch-run` to see full plan/apply output

## Domain References

Load these as needed for detailed operations:

- [workspaces.md](references/workspaces.md) - Workspace management details
- [runs.md](references/runs.md) - Run status and lifecycle
- [providers.md](references/providers.md) - Provider documentation lookup

```text

**Step 2: Commit SKILL.md**

```bash
git add fzymgc-house/skills/terraform/SKILL.md
git commit -m "docs(terraform): complete SKILL.md with RFC2119 keywords

- Full usage documentation for all workflows
- Configuration requirements (MUST/MAY)
- Best practices with SHOULD/MUST NOT directives
- Quick reference table"
```

---

## Task 11: Write Reference Documentation

**Files:**

- Modify: `fzymgc-house/skills/terraform/references/workspaces.md`
- Modify: `fzymgc-house/skills/terraform/references/runs.md`
- Modify: `fzymgc-house/skills/terraform/references/providers.md`

**Step 1: Write workspaces.md**

```markdown
# Workspace Operations Reference

## Workspace Status Fields

| Field | Description |
|-------|-------------|
| `id` | Workspace ID (ws-xxx) |
| `name` | Workspace name |
| `terraform_version` | Configured Terraform version |
| `execution_mode` | remote, local, or agent |
| `auto_apply` | Whether runs auto-apply |
| `working_directory` | Subdirectory for Terraform files |
| `vcs_repo` | VCS connection details |
| `updated_at` | Last modification timestamp |

## Common Workspace Operations

### Get All Workspaces

```bash
terraform_mcp.py workspace-status
```
```

```text

### Get Single Workspace Detail

```bash
terraform_mcp.py workspace-status <workspace-name>
```

### Filter Workspaces (via raw tool)

```bash
terraform_mcp.py tool list_workspaces '{"terraform_org_name":"myorg","search_query":"prod"}'
```

## Underlying MCP Tools

- `list_workspaces` - List/search workspaces
- `get_workspace_details` - Get detailed workspace info

```text

**Step 2: Write runs.md**

```markdown
# Run Operations Reference

## Run Status Lifecycle

```

pending → planning → planned → [cost_estimating →] [policy_checking →] confirmed → applying → applied
                  ↓ ↓
              errored                                                        errored
                  ↓ ↓
              discarded discarded

```text

## Terminal States

| Status | Exit Code | Description |
|--------|-----------|-------------|
| `applied` | 0 | Successfully applied |
| `planned_and_finished` | 0 | Plan-only run completed |
| `errored` | 1 | Run failed |
| `discarded` | 1 | Run was discarded |
| `canceled` | 1 | Run was canceled |

## Run Fields

| Field | Description |
|-------|-------------|
| `id` | Run ID (run-xxx) |
| `status` | Current status |
| `message` | Commit message or description |
| `resource-additions` | Resources to add |
| `resource-changes` | Resources to change |
| `resource-destructions` | Resources to destroy |
| `created-at` | Run creation time |

## Underlying MCP Tools

- `list_runs` - List runs for workspace
- `get_run_details` - Get detailed run info

## Direct HCP API

For log streaming, the skill uses direct HCP Terraform API:
- `GET /api/v2/plans/:id` - Get plan with log URL
- `GET /api/v2/applies/:id` - Get apply with log URL
```

**Step 3: Write providers.md**

```markdown
# Provider Documentation Reference

## Provider Namespaces

Common provider namespaces:

| Provider | Namespace |
|----------|-----------|
| aws, azurerm, google, kubernetes, helm, vault | hashicorp |
| cloudflare | cloudflare |
| datadog | DataDog |
| github | integrations |

## Document Types

| Type | Description |
|------|-------------|
| `overview` | Provider overview and configuration |
| `resources` | Resource documentation |
| `data-sources` | Data source documentation |
| `guides` | Usage guides |
| `functions` | Provider functions |

## Looking Up Resources

### Find Resource Name

```bash
# List available resources
terraform_mcp.py provider-docs aws --list-resources

# Search in output for the resource you need
```
```


```text

### Get Resource Documentation

```bash
# Use exact resource name (without provider prefix)
terraform_mcp.py provider-docs aws --resource lambda_function
terraform_mcp.py provider-docs aws --resource s3_bucket
terraform_mcp.py provider-docs azurerm --resource virtual_machine
```

## Underlying MCP Tools

- `search_providers` - Find provider docs by service name
- `get_provider_details` - Get full documentation content
- `get_latest_provider_version` - Get latest provider version

```text

**Step 4: Commit reference docs**

```bash
git add fzymgc-house/skills/terraform/references/
git commit -m "docs(terraform): add reference documentation

- workspaces.md: workspace fields and operations
- runs.md: run lifecycle and status codes
- providers.md: namespaces and lookup patterns"
```

---

## Task 12: Final Testing and Cleanup

**Step 1: Verify script runs without errors**

```bash
cd /Volumes/Code/github.com/fzymgc-house/fzymgc-house-skills

# Check Python syntax
python3 -m py_compile fzymgc-house/skills/terraform/scripts/terraform_mcp.py

# Check help
fzymgc-house/skills/terraform/scripts/terraform_mcp.py --help
```

**Step 2: Test with real credentials (if available)**

```bash
export TFE_TOKEN="your-token"
export TFE_ORG="your-org"

# Test workspace-status
fzymgc-house/skills/terraform/scripts/terraform_mcp.py workspace-status

# Test list-runs
fzymgc-house/skills/terraform/scripts/terraform_mcp.py list-runs <workspace-name>
```

**Step 3: Final commit**

```bash
git add -A
git status

# If any uncommitted changes:
git commit -m "chore(terraform): final cleanup and testing"
```

**Step 4: Summary commit**

```bash
git log --oneline -10
```

Expected: Series of commits implementing the terraform skill.

---

## Summary

This implementation plan creates:

1. **Directory structure** with SKILL.md, scripts, and references
2. **terraform_mcp.py** gateway script with:
   - MCP stdio client for JSON-RPC to Docker container
   - Session management for container lifecycle
   - Direct HCP API client for log streaming
   - Workflows: workspace-status, list-runs, watch-run, run-outputs, provider-docs, list-providers
3. **SKILL.md** with RFC2119 keywords and comprehensive usage docs
4. **Reference documentation** for workspaces, runs, and providers

Total estimated time: 2-3 hours for complete implementation.
