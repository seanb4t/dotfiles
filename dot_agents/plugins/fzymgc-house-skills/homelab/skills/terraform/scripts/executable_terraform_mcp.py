#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx[socks]",  # [socks] extra needed for SOCKS proxy support (httpx auto-detects proxies from env)
#   "pyyaml"
# ]
# ///
"""
Terraform MCP Gateway Script.

Invokes Terraform MCP server on-demand without loading tool definitions into context.

Run with --help for usage. Requires TFE_TOKEN environment variable.

NOTE: httpx automatically detects proxy configuration from environment variables
(HTTP_PROXY, HTTPS_PROXY, ALL_PROXY) and system settings. The httpx[socks] extra
is required when a SOCKS proxy is detected. If you don't need proxy support,
set NO_PROXY=* in your environment.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import warnings
from typing import Any

import httpx
import yaml

# Configuration
DEFAULT_TFE_ADDRESS = "https://app.terraform.io"
DOCKER_IMAGE = "hashicorp/terraform-mcp-server:0.3.3"
POLL_INTERVAL = 5  # seconds


class MCPStdioClient:
    """MCP client communicating via stdio with Docker container."""

    def __init__(self, proc: subprocess.Popen):
        self._proc = proc
        self._request_id = 0
        self._initialized = False

    def _send(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send JSON-RPC request and receive response."""
        # Check if process is still running
        if self._proc.poll() is not None:
            stderr_output = ""
            if self._proc.stderr:
                stderr_output = self._proc.stderr.read().decode(errors="replace")
            error_msg = f"MCP server process exited (code {self._proc.returncode})"
            if stderr_output:
                error_msg += f": {stderr_output[:500]}"
            return {"error": {"message": error_msg}}

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }

        try:
            line = json.dumps(request) + "\n"
            self._proc.stdin.write(line.encode())
            self._proc.stdin.flush()

            response_line = self._proc.stdout.readline()
            if not response_line:
                # Try to get stderr for better error message
                stderr_output = ""
                if self._proc.stderr:
                    stderr_output = self._proc.stderr.read().decode(errors="replace")
                error_msg = "No response from MCP server"
                if stderr_output:
                    error_msg += f": {stderr_output[:500]}"
                return {"error": {"message": error_msg}}

            return json.loads(response_line)
        except BrokenPipeError as e:
            return {"error": {"message": f"Connection to MCP server broken: {e}"}}
        except json.JSONDecodeError as e:
            return {"error": {"message": f"Invalid JSON response from MCP server: {e}"}}

    def initialize(self) -> dict[str, Any]:
        """Initialize the MCP session."""
        if self._initialized:
            return {"success": True}

        result = self._send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "terraform-mcp-gateway", "version": "1.0.0"},
            },
        )

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
            return {
                "success": False,
                "error": result["error"].get("message", str(result["error"])),
            }

        if "result" in result and "tools" in result["result"]:
            tool_names = [t["name"] for t in result["result"]["tools"]]
            return {"success": True, "tools": sorted(tool_names)}

        return {"success": False, "error": f"Unexpected response: {result}"}

    def describe_tool(self, tool_name: str) -> dict[str, Any]:
        """Get schema for a specific tool."""
        self.initialize()
        result = self._send("tools/list")

        if "error" in result:
            return {
                "success": False,
                "error": result["error"].get("message", str(result["error"])),
            }

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
            return {
                "success": False,
                "error": result["error"].get("message", str(result["error"])),
            }

        if "result" in result:
            return {"success": True, "result": result["result"]}

        return {"success": False, "error": f"Unexpected response: {result}"}

    def close(self):
        """Terminate the MCP server process."""
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()


class SessionManager:
    """Manage Docker container session for MCP server."""

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._client: MCPStdioClient | None = None
        self._env_file_path: str | None = None

    def _get_env(self) -> dict[str, str]:
        """Get environment variables for Docker container."""
        token = os.environ.get("TFE_TOKEN")
        if not token:
            raise EnvironmentError(
                "TFE_TOKEN environment variable is required. "
                "Create a token at https://app.terraform.io/app/settings/tokens"
            )

        address = os.environ.get("TFE_ADDRESS", DEFAULT_TFE_ADDRESS)

        return {
            "TFE_TOKEN": token,
            "TFE_ADDRESS": address,
        }

    def _spawn_container(self) -> subprocess.Popen:
        """Spawn a new Docker container."""
        env = self._get_env()

        # Write env vars to temp file to avoid exposing token in process list
        env_file = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
        # Assign path immediately so cleanup can find it if write/close fails
        self._env_file_path = env_file.name
        try:
            env_file.write(f"TFE_TOKEN={env['TFE_TOKEN']}\n")
            env_file.write(f"TFE_ADDRESS={env['TFE_ADDRESS']}\n")
            env_file.close()

            cmd = [
                "docker",
                "run",
                "-i",
                "--rm",
                "--env-file",
                self._env_file_path,
                DOCKER_IMAGE,
            ]

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            return proc
        except Exception:
            # Clean up temp file on any error during spawn
            if self._env_file_path and os.path.exists(self._env_file_path):
                os.unlink(self._env_file_path)
                self._env_file_path = None
            raise

    def get_client(self) -> MCPStdioClient:
        """Get or create MCP client."""
        self._proc = self._spawn_container()
        self._client = MCPStdioClient(self._proc)
        return self._client

    def cleanup(self):
        """Clean up resources."""
        # Close MCP client first
        if self._client:
            self._client.close()
            self._client = None

        # Terminate container process (redundant but safe)
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

        # Remove temp env file
        if self._env_file_path and os.path.exists(self._env_file_path):
            os.unlink(self._env_file_path)
            self._env_file_path = None


class HCPTerraformClient:
    """Direct HCP Terraform API client for operations not exposed via MCP."""

    def __init__(self, token: str, address: str = DEFAULT_TFE_ADDRESS):
        if not token:
            raise ValueError("HCP Terraform API token is required")
        self._client = httpx.Client(
            base_url=address.rstrip("/"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/vnd.api+json",
            },
            timeout=30.0,
        )

    def get_plan_logs(self, plan_id: str) -> dict[str, Any]:
        """Fetch plan logs from HCP Terraform API."""
        try:
            resp = self._client.get(f"/api/v2/plans/{plan_id}")
            resp.raise_for_status()
            plan_data = resp.json()

            log_url = (
                plan_data.get("data", {}).get("attributes", {}).get("log-read-url")
            )
            if not log_url:
                return {"success": False, "error": "No log URL available"}

            log_resp = httpx.get(log_url, timeout=30.0)
            log_resp.raise_for_status()
            return {"success": True, "logs": log_resp.text}
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            }
        except httpx.TimeoutException as e:
            return {"success": False, "error": f"Request timed out: {e}"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}

    def get_apply_logs(self, apply_id: str) -> dict[str, Any]:
        """Fetch apply logs from HCP Terraform API."""
        try:
            resp = self._client.get(f"/api/v2/applies/{apply_id}")
            resp.raise_for_status()
            apply_data = resp.json()

            log_url = (
                apply_data.get("data", {}).get("attributes", {}).get("log-read-url")
            )
            if not log_url:
                return {"success": False, "error": "No log URL available"}

            log_resp = httpx.get(log_url, timeout=30.0)
            log_resp.raise_for_status()
            return {"success": True, "logs": log_resp.text}
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            }
        except httpx.TimeoutException as e:
            return {"success": False, "error": f"Request timed out: {e}"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}

    def get_run(self, run_id: str) -> dict[str, Any]:
        """Get run details including plan/apply IDs."""
        try:
            resp = self._client.get(f"/api/v2/runs/{run_id}")
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            }
        except httpx.TimeoutException as e:
            return {"success": False, "error": f"Request timed out: {e}"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}

    def list_runs(
        self,
        organization: str,
        workspace: str,
        page_size: int = 10,
        status_filter: str | None = None,
    ) -> dict[str, Any]:
        """List runs for a workspace via direct HCP API.

        This method exists because the MCP server's list_runs tool is broken
        (returns empty/malformed data for all queries).
        """
        try:
            params: dict[str, Any] = {
                "filter[organization][name]": organization,
                "filter[workspace][name]": workspace,
                "page[size]": page_size,
            }
            if status_filter:
                params["filter[status]"] = status_filter

            resp = self._client.get("/api/v2/runs", params=params)
            resp.raise_for_status()
            return {"success": True, "data": resp.json()}
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            }
        except httpx.TimeoutException as e:
            return {"success": False, "error": f"Request timed out: {e}"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Network error: {e}"}

    def close(self):
        """Close the HTTP client."""
        self._client.close()


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
                    warnings.warn("MCP response text is not valid JSON, using raw text")
                    texts.append(item["text"])

        if len(texts) == 1:
            return texts[0]
        return texts

    return result


def parse_provider_search_markdown(
    text: str, target_slug: str | None = None
) -> list[dict]:
    """Parse markdown response from search_providers into structured data.

    The MCP server returns markdown formatted like:
    - providerDocID: 10931109
    - Title: lambda_function
    - Category: resources
    - Description: Manages an AWS Lambda Function.
    ---

    Returns list of dicts with id, title, category, description.
    If target_slug is provided, prioritizes exact title matches.
    """
    entries = []
    current = {}

    for line in text.split("\n"):
        line = line.strip()
        if line == "---":
            if current:
                entries.append(current)
                current = {}
        elif line.startswith("- providerDocID:"):
            current["id"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Title:"):
            current["title"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Category:"):
            current["category"] = line.split(":", 1)[1].strip()
        elif line.startswith("- Description:"):
            current["description"] = line.split(":", 1)[1].strip()

    # Don't forget the last entry if no trailing ---
    if current:
        entries.append(current)

    # If we have a target slug, prioritize exact matches
    if target_slug and entries:
        exact_matches = [
            e for e in entries if e.get("title", "").lower() == target_slug.lower()
        ]
        if exact_matches:
            return exact_matches

    return entries


def format_output(data: Any, fmt: str) -> str:
    """Format output according to specified format."""
    if fmt == "json":
        return json.dumps(data, separators=(",", ":"))
    elif fmt == "yaml":
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    else:  # compact
        return yaml.dump(data, default_flow_style=True, sort_keys=False)


def format_terraform_logs(raw_logs: str) -> str:
    """Format Terraform JSON logs as human-readable markdown.

    Parses JSON diagnostic messages and formats them for reduced token usage.
    Non-JSON lines are passed through as-is.
    """
    lines = []
    for line in raw_logs.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Try to parse as JSON
        if line.startswith("{"):
            try:
                obj = json.loads(line)
                msg_type = obj.get("type", "")
                level = obj.get("@level", "info")
                message = obj.get("@message", "")

                if msg_type == "diagnostic":
                    # Format error/warning diagnostics
                    diag = obj.get("diagnostic", {})
                    severity = diag.get("severity", level).upper()
                    summary = diag.get("summary", message)
                    detail = diag.get("detail", "")
                    range_info = diag.get("range", {})

                    formatted = f"{severity}: {summary}"
                    if range_info:
                        filename = range_info.get("filename", "")
                        start = range_info.get("start", {})
                        line_num = start.get("line", "")
                        col = start.get("column", "")
                        if filename:
                            formatted += f"\n  File: {filename}:{line_num}:{col}"
                    if detail:
                        formatted += f"\n  Detail: {detail}"
                    lines.append(formatted)

                elif msg_type == "change_summary":
                    # Format plan/apply summary
                    changes = obj.get("changes", {})
                    op = changes.get("operation", "")
                    add = changes.get("add", 0)
                    change = changes.get("change", 0)
                    remove = changes.get("remove", 0)
                    if op == "plan":
                        lines.append(
                            f"Plan: {add} to add, {change} to change, {remove} to destroy"
                        )
                    elif op == "apply":
                        lines.append(
                            f"Apply complete: {add} added, {change} changed, {remove} destroyed"
                        )
                    else:
                        lines.append(message)

                elif msg_type == "version":
                    # Terraform version info
                    tf_version = obj.get("terraform", "")
                    lines.append(f"Terraform v{tf_version}")

                elif msg_type == "resource_drift" or msg_type == "planned_change":
                    # Resource changes - just use the message
                    lines.append(message)

                elif message:
                    # Other messages - just print the message
                    lines.append(message)

            except json.JSONDecodeError:
                # Not valid JSON, include as-is
                lines.append(line)
        else:
            # Non-JSON line, include as-is
            lines.append(line)

    return "\n".join(lines)


def get_default_org() -> str:
    """Get default organization from environment."""
    org = os.environ.get("TFE_ORG")
    if not org:
        raise EnvironmentError(
            "TFE_ORG environment variable is required for workspace/run operations. "
            "Set it to your HCP Terraform organization name (e.g., export TFE_ORG=my-org)"
        )
    return org


def _truncate_message(msg: str, max_len: int) -> str:
    """Truncate message with ellipsis if too long."""
    if len(msg) <= max_len:
        return msg
    return msg[: max_len - 3] + "..."


def workflow_workspace_status(
    client: MCPStdioClient, args: argparse.Namespace, fmt: str
) -> int:
    """Show workspace status overview."""
    org = get_default_org()
    workspace_name = getattr(args, "workspace", None)

    if workspace_name:
        # Single workspace detail
        result = client.call_tool(
            "get_workspace_details",
            {
                "terraform_org_name": org,
                "workspace_name": workspace_name,
            },
        )

        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)
        if not isinstance(data, dict):
            print("Error: Unexpected response format", file=sys.stderr)
            return 1

        # Extract key fields
        output = {
            "workspace": workspace_name,
            "organization": org,
            "workspace_id": data.get("id", ""),
            "terraform_version": data.get("attributes", {}).get(
                "terraform-version", ""
            ),
            "execution_mode": data.get("attributes", {}).get("execution-mode", ""),
            "auto_apply": data.get("attributes", {}).get("auto-apply", False),
            "working_directory": data.get("attributes", {}).get(
                "working-directory", ""
            ),
            "vcs_repo": data.get("attributes", {}).get("vcs-repo", {}),
            "updated_at": data.get("attributes", {}).get("updated-at", ""),
        }

        print(format_output(output, fmt))
        return 0

    else:
        # List all workspaces
        result = client.call_tool(
            "list_workspaces",
            {
                "terraform_org_name": org,
            },
        )

        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)

        # Validate data type before processing
        if not isinstance(data, (dict, list)):
            print(
                f"Error: Unexpected response format: {type(data).__name__}",
                file=sys.stderr,
            )
            return 1

        # Handle various response structures from MCP
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "data" in data:
            if isinstance(data["data"], list):
                items = data["data"]
            else:
                warnings.warn(
                    f"Expected list in data['data'], got {type(data['data']).__name__}. Using empty list.",
                    stacklevel=2,
                )
                items = []
        elif isinstance(data, dict) and "items" in data:
            if isinstance(data["items"], list):
                items = data["items"]
            else:
                warnings.warn(
                    f"Expected list in data['items'], got {type(data['items']).__name__}. Using empty list.",
                    stacklevel=2,
                )
                items = []
        elif isinstance(data, dict):
            items = [data]  # Single workspace response
        else:
            print(
                "Error: Could not extract workspace list from response", file=sys.stderr
            )
            return 1

        # Format as brief list
        workspaces = []
        for ws in items:
            attrs = ws.get("attributes", {}) if isinstance(ws, dict) else {}
            workspaces.append(
                {
                    "name": attrs.get("name", ws.get("name", "")),
                    "id": ws.get("id", ""),
                    "terraform_version": attrs.get("terraform-version", ""),
                    "updated_at": attrs.get("updated-at", ""),
                }
            )

        output = {
            "organization": org,
            "count": len(workspaces),
            "workspaces": workspaces,
        }

        print(format_output(output, fmt))
        return 0


def _is_mcp_list_runs_broken(data: Any) -> bool:
    """Check if MCP list_runs returned broken/empty data.

    The MCP server has a known bug where it returns {"data":{"type":""}}
    instead of the actual runs list.
    """
    if not isinstance(data, dict):
        return False
    if "data" not in data:
        return False
    # Broken response: {"data":{"type":""}} instead of {"data":[...]}
    if isinstance(data["data"], dict) and data["data"].get("type") == "":
        return True
    return False


def _extract_runs_from_api_response(data: Any) -> list[dict]:
    """Extract runs list from API response data."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
    return []


def workflow_list_runs(
    client: MCPStdioClient, args: argparse.Namespace, fmt: str
) -> int:
    """List recent runs for a workspace."""
    org = get_default_org()
    workspace = getattr(args, "workspace", None)
    if not workspace:
        print("Error: workspace argument is required", file=sys.stderr)
        return 1
    limit = getattr(args, "limit", 10)
    status_filter = getattr(args, "status", None)

    # Try MCP first
    params: dict[str, Any] = {
        "terraform_org_name": org,
        "workspace_name": workspace,
        "pageSize": limit,
    }
    if status_filter:
        params["status"] = [status_filter]

    result = client.call_tool("list_runs", params)
    items: list[dict] = []
    used_fallback = False

    if result.get("success"):
        data = unwrap_result(result)
        if _is_mcp_list_runs_broken(data):
            # MCP server bug: returns {"data":{"type":""}} - fall back to direct API
            used_fallback = True
        elif isinstance(data, (dict, list)):
            items = _extract_runs_from_api_response(data)

    # Fall back to direct HCP API if MCP failed or returned broken data
    if not items and (not result.get("success") or used_fallback):
        token = os.environ.get("TFE_TOKEN")
        address = os.environ.get("TFE_ADDRESS", DEFAULT_TFE_ADDRESS)
        if not token:
            print("Error: TFE_TOKEN required for direct API fallback", file=sys.stderr)
            return 1

        hcp_client = HCPTerraformClient(token, address)
        try:
            api_result = hcp_client.list_runs(org, workspace, limit, status_filter)
            if not api_result.get("success"):
                print(f"Error: {api_result.get('error')}", file=sys.stderr)
                return 1
            api_data = api_result.get("data", {})
            items = _extract_runs_from_api_response(api_data)
        finally:
            hcp_client.close()

    runs = []
    for run in items:
        attrs = run.get("attributes", {}) if isinstance(run, dict) else {}
        runs.append(
            {
                "id": run.get("id", ""),
                "status": attrs.get("status", ""),
                "message": _truncate_message(attrs.get("message", "") or "", 80),
                "created_at": attrs.get("created-at", ""),
                "plan_only": attrs.get("plan-only", False),
                "is_destroy": attrs.get("is-destroy", False),
            }
        )

    # Use compact table format by default, YAML/JSON for explicit format requests
    if fmt == "compact" or fmt == "yaml":
        # Compact table output
        print(f"Workspace: {workspace} ({org})")
        print(f"Runs: {len(runs)}")
        print()
        # Header
        print(f"{'ID':<24} {'STATUS':<12} {'CREATED':<17} MESSAGE")
        print("-" * 80)
        for run in runs:
            # Parse and format created_at
            created = (
                run["created_at"][:16].replace("T", " ") if run["created_at"] else ""
            )
            # First line of message only
            msg = run["message"].split("\n")[0][:40]
            status = run["status"]
            # Add markers for special runs
            if run["is_destroy"]:
                status += " 🗑"
            elif run["plan_only"]:
                status += " 📋"
            print(f"{run['id']:<24} {status:<12} {created:<17} {msg}")
    else:
        # JSON format - structured output
        output = {
            "workspace": workspace,
            "organization": org,
            "count": len(runs),
            "runs": runs,
        }
        print(format_output(output, fmt))

    return 0


def workflow_list_providers(
    client: MCPStdioClient, args: argparse.Namespace, fmt: str
) -> int:
    """List/search available providers."""
    search = getattr(args, "search", None) or ""
    namespace = getattr(args, "namespace", None) or "hashicorp"

    # Use search_providers with overview type to list
    result = client.call_tool(
        "search_providers",
        {
            "provider_name": search if search else "aws",  # Default search term
            "provider_namespace": namespace,
            "service_slug": search if search else "aws",
            "provider_document_type": "overview",
        },
    )

    if not result.get("success"):
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return 1

    data = unwrap_result(result)

    # Validate data type
    if not isinstance(data, (dict, list)):
        print(
            f"Error: Unexpected response format: {type(data).__name__}", file=sys.stderr
        )
        return 1

    # Format as list
    items = data if isinstance(data, list) else [data]
    providers = []
    for item in items:
        if isinstance(item, dict):
            providers.append(
                {
                    "name": item.get("title", ""),
                    "id": item.get("id", ""),
                    "category": item.get("category", ""),
                }
            )

    output = {
        "search": search,
        "namespace": namespace,
        "count": len(providers),
        "providers": providers,
    }

    print(format_output(output, fmt))
    return 0


def workflow_provider_docs(
    client: MCPStdioClient, args: argparse.Namespace, fmt: str
) -> int:
    """Look up provider documentation."""
    provider = args.provider
    resource = getattr(args, "resource", None)
    data_source = getattr(args, "data_source", None)
    list_resources = getattr(args, "list_resources", False)

    # Validate mutually exclusive arguments
    if sum(bool(x) for x in [resource, data_source, list_resources]) > 1:
        print(
            "Error: Only one of --resource, --data-source, or --list-resources can be used",
            file=sys.stderr,
        )
        return 1

    # Determine namespace (default to hashicorp for common providers)
    namespace = getattr(args, "namespace", None)

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

    if not namespace and provider in provider_namespaces:
        namespace = provider_namespaces[provider]
    elif not namespace:
        namespace = "hashicorp"  # Default fallback

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
    result = client.call_tool(
        "search_providers",
        {
            "provider_name": provider,
            "provider_namespace": namespace,
            "service_slug": service_slug,
            "provider_document_type": doc_type,
        },
    )

    if not result.get("success"):
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return 1

    data = unwrap_result(result)

    # Handle markdown response from search_providers
    # The MCP server returns markdown text, not JSON
    if isinstance(data, str):
        parsed_entries = parse_provider_search_markdown(data, service_slug)
        if not parsed_entries:
            print(
                f"No documentation found for {provider}/{service_slug}", file=sys.stderr
            )
            return 1
        data = parsed_entries
    elif not isinstance(data, (dict, list)):
        print(
            f"Error: Unexpected response format: {type(data).__name__}", file=sys.stderr
        )
        return 1

    # If listing resources, just show the search results
    if list_resources:
        items = data if isinstance(data, list) else [data]
        resources = [
            {"title": item.get("title", ""), "id": item.get("id", "")}
            for item in items
            if isinstance(item, dict)
        ]
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
    detail_result = client.call_tool(
        "get_provider_details",
        {
            "provider_doc_id": str(doc_id),
        },
    )

    if not detail_result.get("success"):
        print(f"Error: {detail_result.get('error')}", file=sys.stderr)
        return 1

    doc_data = unwrap_result(detail_result)

    # Output the documentation
    if fmt == "yaml":
        # For YAML, structure the output
        if isinstance(doc_data, str):
            content = doc_data
        elif isinstance(doc_data, dict):
            content = doc_data.get("content", doc_data)
        else:
            content = str(doc_data)

        output = {
            "provider": provider,
            "namespace": namespace,
            "type": doc_type,
            "content": content,
        }
        print(format_output(output, fmt))
    else:
        # For other formats, just print the content
        if isinstance(doc_data, str):
            content = doc_data
        elif isinstance(doc_data, dict):
            content = doc_data.get("content", str(doc_data))
        else:
            content = str(doc_data)
        print(content)

    return 0


def workflow_run_outputs(
    client: MCPStdioClient, args: argparse.Namespace, fmt: str
) -> int:
    """View terraform outputs from a run."""
    org = get_default_org()
    run_id = getattr(args, "run_id", None)
    workspace = getattr(args, "workspace", None)

    # If workspace provided, get latest successful run
    if not run_id and workspace:
        result = client.call_tool(
            "list_runs",
            {
                "terraform_org_name": org,
                "workspace_name": workspace,
                "pageSize": 10,
                "status": ["applied"],
            },
        )
        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)

        # Validate data type
        if not isinstance(data, (dict, list)):
            print(
                f"Error: Unexpected response format: {type(data).__name__}",
                file=sys.stderr,
            )
            return 1

        # Handle various response structures
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "data" in data:
            if isinstance(data["data"], list):
                items = data["data"]
            else:
                warnings.warn(
                    f"Expected list in data['data'], got {type(data['data']).__name__}. Using empty list.",
                    stacklevel=2,
                )
                items = []
        elif isinstance(data, dict) and "items" in data:
            if isinstance(data["items"], list):
                items = data["items"]
            else:
                warnings.warn(
                    f"Expected list in data['items'], got {type(data['items']).__name__}. Using empty list.",
                    stacklevel=2,
                )
                items = []
        else:
            items = []

        if not items:
            print(
                f"No successful runs found for workspace '{workspace}'", file=sys.stderr
            )
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

    # Validate data type
    if not isinstance(data, dict):
        print(
            f"Error: Unexpected response format: {type(data).__name__}", file=sys.stderr
        )
        return 1

    # Extract outputs from run if available
    outputs = data.get("outputs", {})

    if not outputs:
        # Try to get from attributes
        attrs = data.get("attributes", {})
        outputs = attrs.get("outputs", {})

    if not outputs:
        print(f"No outputs found for run {run_id}", file=sys.stderr)
        print(
            "Note: Outputs may only be available after terraform apply", file=sys.stderr
        )
        return 1

    output = {
        "run_id": run_id,
        "outputs": outputs,
    }

    print(format_output(output, fmt))
    return 0


def workflow_run_details(
    client: MCPStdioClient,
    hcp_client: HCPTerraformClient,
    args: argparse.Namespace,
    fmt: str,
) -> int:
    """View details and logs for a completed run."""
    run_id = args.run_id

    # Get run details
    result = client.call_tool("get_run_details", {"run_id": run_id})

    if not result.get("success"):
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return 1

    data = unwrap_result(result)
    if not isinstance(data, dict):
        print("Error: Unexpected response format", file=sys.stderr)
        return 1

    # Navigate into the run object (response wraps it in {"data": {...}})
    run_data = data.get("data", data)
    if isinstance(run_data, dict) and run_data.get("type") == "runs":
        data = run_data

    attrs = data.get("attributes", {})
    status = attrs.get("status", "unknown")
    message = attrs.get("message", "") or ""

    # Print run summary
    print(f"Run: {run_id}")
    print(f"Status: {status}")
    print(f"Message: {_truncate_message(message, 200)}")
    print(
        f"Resources: +{attrs.get('resource-additions', 0)} ~{attrs.get('resource-changes', 0)} -{attrs.get('resource-destructions', 0)}"
    )
    print("-" * 50)

    # Get and display logs
    relationships = data.get("relationships", {})
    if not relationships:
        print("[No relationships data - logs unavailable]", file=sys.stderr)
        return 0

    plan_rel = relationships.get("plan", {}).get("data", {})
    apply_rel = relationships.get("apply", {}).get("data", {})

    if plan_rel.get("id"):
        print("\n=== Plan Output ===")
        log_result = hcp_client.get_plan_logs(plan_rel["id"])
        if log_result.get("success"):
            formatted = format_terraform_logs(log_result.get("logs", ""))
            print(formatted)
        else:
            print(f"[Could not fetch plan logs: {log_result.get('error')}]")

    # Show apply logs for both successful and errored runs
    # (errors during apply have status "errored" not "applied")
    if apply_rel.get("id") and status in ("applied", "errored"):
        print("\n=== Apply Output ===")
        log_result = hcp_client.get_apply_logs(apply_rel["id"])
        if log_result.get("success"):
            formatted = format_terraform_logs(log_result.get("logs", ""))
            print(formatted)
        else:
            print(f"[Could not fetch apply logs: {log_result.get('error')}]")

    return 0


def workflow_watch_run(
    client: MCPStdioClient,
    hcp_client: HCPTerraformClient,
    args: argparse.Namespace,
    fmt: str,
) -> int:
    """Watch a run's progress with live updates."""
    org = get_default_org()
    run_id = getattr(args, "run_id", None)
    workspace = getattr(args, "workspace", None)
    show_logs = getattr(args, "logs", False)
    poll_interval = getattr(args, "interval", POLL_INTERVAL)
    max_wait = getattr(args, "timeout", 3600)
    start_time = time.time()

    # Validate poll_interval (minimum 1 second)
    poll_interval = max(poll_interval, 1)

    # If workspace provided, get latest run
    if not run_id and workspace:
        result = client.call_tool(
            "list_runs",
            {
                "terraform_org_name": org,
                "workspace_name": workspace,
                "pageSize": 1,
            },
        )
        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            if "data" in data:
                if isinstance(data["data"], list):
                    items = data["data"]
                else:
                    warnings.warn(
                        f"Expected list in data['data'], got {type(data['data']).__name__}. Using empty list.",
                        stacklevel=2,
                    )
                    items = []
            elif "items" in data:
                if isinstance(data["items"], list):
                    items = data["items"]
                else:
                    warnings.warn(
                        f"Expected list in data['items'], got {type(data['items']).__name__}. Using empty list.",
                        stacklevel=2,
                    )
                    items = []
            else:
                items = [data] if data else []
        else:
            items = []

        if not items:
            print(f"No runs found for workspace '{workspace}'", file=sys.stderr)
            return 1
        run_id = items[0].get("id")

    if not run_id:
        print("Error: Either run_id or --workspace is required", file=sys.stderr)
        return 1

    terminal_states = {
        "applied",
        "errored",
        "discarded",
        "canceled",
        "force_canceled",
        "planned_and_finished",
        "policy_soft_failed",
    }

    # Check if run is already in terminal state
    result = client.call_tool("get_run_details", {"run_id": run_id})
    if result.get("success"):
        data = unwrap_result(result)
        if isinstance(data, dict):
            run_data = data.get("data", data)
            if isinstance(run_data, dict) and run_data.get("type") == "runs":
                data = run_data
            attrs = data.get("attributes", {})
            status = attrs.get("status", "unknown")
            if status in terminal_states:
                print(
                    f"Run {run_id} is already complete (status: {status})",
                    file=sys.stderr,
                )
                print(
                    f"Use 'run-details {run_id}' to view formatted logs",
                    file=sys.stderr,
                )
                if not show_logs:
                    # Just show summary and exit
                    output = {
                        "run_id": run_id,
                        "status": status,
                        "message": _truncate_message(
                            attrs.get("message", "") or "", 200
                        ),
                        "resource_additions": attrs.get("resource-additions", 0),
                        "resource_changes": attrs.get("resource-changes", 0),
                        "resource_destructions": attrs.get("resource-destructions", 0),
                    }
                    print(format_output(output, fmt))
                    success_states = {"applied", "planned_and_finished"}
                    return 0 if status in success_states else 1

    print(f"Watching run: {run_id}", file=sys.stderr)
    print(f"Poll interval: {poll_interval}s", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    last_status = None

    while True:
        # Check for timeout
        if time.time() - start_time > max_wait:
            print(f"Timeout: Run did not complete within {max_wait}s", file=sys.stderr)
            return 1

        result = client.call_tool("get_run_details", {"run_id": run_id})

        if not result.get("success"):
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1

        data = unwrap_result(result)
        if not isinstance(data, dict):
            print("Error: Unexpected response format", file=sys.stderr)
            return 1

        # Navigate into the run object (response wraps it in {"data": {...}})
        run_data = data.get("data", data)
        if isinstance(run_data, dict) and run_data.get("type") == "runs":
            data = run_data

        attrs = data.get("attributes", {})
        status = attrs.get("status", "unknown")

        # Print status update if changed
        if status != last_status:
            timestamp = time.strftime("%H:%M:%S")
            plan_summary = ""

            # Try to get plan/apply counts
            additions = attrs.get("resource-additions", 0)
            changes = attrs.get("resource-changes", 0)
            destructions = attrs.get("resource-destructions", 0)
            if additions or changes or destructions:
                plan_summary = f" | Plan: +{additions} ~{changes} -{destructions}"

            print(f"[{timestamp}] Status: {status}{plan_summary}", file=sys.stderr)
            last_status = status

        # Check for terminal state
        if status in terminal_states:
            print("-" * 50, file=sys.stderr)

            # Get and display logs if requested
            if show_logs:
                relationships = data.get("relationships", {})
                if not relationships:
                    print("[No relationships data - logs unavailable]", file=sys.stderr)
                else:
                    plan_rel = relationships.get("plan", {}).get("data", {})
                    apply_rel = relationships.get("apply", {}).get("data", {})

                    if plan_rel.get("id"):
                        print("\n=== Plan Output ===")
                        log_result = hcp_client.get_plan_logs(plan_rel["id"])
                        if log_result.get("success"):
                            formatted = format_terraform_logs(
                                log_result.get("logs", "")
                            )
                            print(formatted)
                        else:
                            print(
                                f"[Could not fetch plan logs: {log_result.get('error')}]"
                            )

                    # Show apply logs for both successful and errored runs
                    if apply_rel.get("id") and status in ("applied", "errored"):
                        print("\n=== Apply Output ===")
                        log_result = hcp_client.get_apply_logs(apply_rel["id"])
                        if log_result.get("success"):
                            formatted = format_terraform_logs(
                                log_result.get("logs", "")
                            )
                            print(formatted)
                        else:
                            print(
                                f"[Could not fetch apply logs: {log_result.get('error')}]"
                            )

            # Final output
            output = {
                "run_id": run_id,
                "status": status,
                "message": _truncate_message(attrs.get("message", "") or "", 200),
                "resource_additions": attrs.get("resource-additions", 0),
                "resource_changes": attrs.get("resource-changes", 0),
                "resource_destructions": attrs.get("resource-destructions", 0),
            }

            if fmt != "compact":
                print(format_output(output, fmt))

            # Success states return 0, failure states return 1
            success_states = {"applied", "planned_and_finished"}
            return 0 if status in success_states else 1

        time.sleep(poll_interval)


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
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list-tools
    subparsers.add_parser("list-tools", help="List available MCP tools")

    # describe
    describe_parser = subparsers.add_parser("describe", help="Describe a tool's schema")
    describe_parser.add_argument("name", help="Tool name")

    # tool (raw tool call)
    tool_parser = subparsers.add_parser("tool", help="Call an MCP tool directly")
    tool_parser.add_argument("name", help="Tool name")
    tool_parser.add_argument(
        "arguments", nargs="?", default="{}", help="JSON arguments"
    )

    # workspace-status
    ws_parser = subparsers.add_parser("workspace-status", help="Show workspace status")
    ws_parser.add_argument(
        "workspace", nargs="?", help="Workspace name (optional, lists all if omitted)"
    )

    # list-runs
    runs_parser = subparsers.add_parser(
        "list-runs", help="List recent runs for a workspace"
    )
    runs_parser.add_argument("workspace", help="Workspace name")
    runs_parser.add_argument(
        "--limit", type=int, default=10, help="Number of runs (default: 10)"
    )
    runs_parser.add_argument(
        "--status", help="Filter by status (e.g., applied, errored, planning)"
    )

    # watch-run
    watch_parser = subparsers.add_parser("watch-run", help="Watch a run's progress")
    watch_parser.add_argument("run_id", nargs="?", help="Run ID to watch")
    watch_parser.add_argument(
        "--workspace", "-w", help="Watch latest run for workspace"
    )
    watch_parser.add_argument(
        "--logs", "-l", action="store_true", help="Show plan/apply logs when complete"
    )
    watch_parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=5,
        help="Poll interval in seconds (default: 5)",
    )
    watch_parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=3600,
        help="Maximum wait time in seconds (default: 3600)",
    )

    # run-outputs
    outputs_parser = subparsers.add_parser(
        "run-outputs", help="View terraform outputs from a run"
    )
    outputs_parser.add_argument("run_id", nargs="?", help="Run ID")
    outputs_parser.add_argument(
        "--workspace", "-w", help="Get outputs from latest successful run"
    )

    # run-details
    details_parser = subparsers.add_parser(
        "run-details", help="View details and formatted logs for a completed run"
    )
    details_parser.add_argument("run_id", help="Run ID to inspect")

    # list-providers
    list_prov_parser = subparsers.add_parser(
        "list-providers", help="List/search providers"
    )
    list_prov_parser.add_argument("--search", "-s", help="Search term")
    list_prov_parser.add_argument(
        "--namespace", "-n", default="hashicorp", help="Provider namespace"
    )

    # provider-docs
    provider_parser = subparsers.add_parser(
        "provider-docs", help="Look up provider documentation"
    )
    provider_parser.add_argument(
        "provider", help="Provider name (e.g., aws, azurerm, google)"
    )
    provider_parser.add_argument(
        "--namespace", help="Provider namespace (default: auto-detected)"
    )
    provider_parser.add_argument(
        "--resource", "-r", help="Resource name (e.g., lambda_function)"
    )
    provider_parser.add_argument("--data-source", "-d", help="Data source name")
    provider_parser.add_argument(
        "--list-resources", "-l", action="store_true", help="List available resources"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    session = SessionManager()
    hcp_client = None

    try:
        client = session.get_client()

        # Create HCP client for direct API calls
        token = os.environ.get("TFE_TOKEN")
        address = os.environ.get("TFE_ADDRESS", DEFAULT_TFE_ADDRESS)
        if token:
            hcp_client = HCPTerraformClient(token, address)

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

        elif args.command == "workspace-status":
            sys.exit(workflow_workspace_status(client, args, args.format))

        elif args.command == "list-runs":
            sys.exit(workflow_list_runs(client, args, args.format))

        elif args.command == "watch-run":
            if not hcp_client:
                print("Error: TFE_TOKEN required for watch-run", file=sys.stderr)
                sys.exit(1)
            sys.exit(workflow_watch_run(client, hcp_client, args, args.format))

        elif args.command == "run-outputs":
            sys.exit(workflow_run_outputs(client, args, args.format))

        elif args.command == "run-details":
            if not hcp_client:
                print("Error: TFE_TOKEN required for run-details", file=sys.stderr)
                sys.exit(1)
            sys.exit(workflow_run_details(client, hcp_client, args, args.format))

        elif args.command == "list-providers":
            sys.exit(workflow_list_providers(client, args, args.format))

        elif args.command == "provider-docs":
            sys.exit(workflow_provider_docs(client, args, args.format))

    except EnvironmentError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.cleanup()
        if hcp_client:
            hcp_client.close()


if __name__ == "__main__":
    main()
