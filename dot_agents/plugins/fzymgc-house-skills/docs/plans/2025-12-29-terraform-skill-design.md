# Terraform Skill Design

**Date:** 2025-12-29  
**Status:** Draft  
**Author:** Claude (AI-assisted design)

## Overview

Create a skill that wraps the HashiCorp Terraform MCP server to provide streamlined Terraform Cloud operations and registry documentation lookup, without exposing the full MCP tool surface to Claude's context.

## Goals

1. **Ease of TFC operations**: Watch runs, view plan/apply logs, check workspace status
2. **Documentation lookup**: Provider discovery, resource documentation
3. **Minimal context overhead**: Only skill docs load into context, not 30+ MCP tool definitions
4. **Secure token handling**: TFE_TOKEN passed via environment variable to subprocess

## Non-Goals

- Destructive operations (create/delete workspaces, apply runs)
- Variable management
- Private registry module/provider management
- Full MCP tool exposure

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  Claude Context                                             │
│  ┌─────────────────┐                                        │
│  │ terraform/      │                                        │
│  │  SKILL.md       │  ◄── Only this loads into context      │
│  └────────┬────────┘                                        │
└───────────┼─────────────────────────────────────────────────┘
            │ Bash invocation
            ▼
┌─────────────────────────────────────────────────────────────┐
│  terraform_mcp.py (uv run)                                  │
│  ├── Session management (reuse Docker process)              │
│  ├── MCP client (stdio JSON-RPC to Docker container)        │
│  ├── Direct HCP API client (for log streaming)              │
│  └── Compound workflows                                     │
└─────────────────────────────────────────────────────────────┘
            │ stdio JSON-RPC
            ▼
┌─────────────────────────────────────────────────────────────┐
│  docker run hashicorp/terraform-mcp-server:0.3.3            │
│  (spawned as subprocess, kept alive for session)            │
└─────────────────────────────────────────────────────────────┘
```

### Why Hybrid Client?

The Terraform MCP server's `get_run_details` tool may not expose full plan/apply log output. The HCP Terraform API provides dedicated streaming endpoints:

- `GET /plans/:plan_id/logs` - Plan log output
- `GET /applies/:apply_id/logs` - Apply log output

The gateway script MUST support direct HCP API calls as a fallback for log retrieval.

## Configuration

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `TFE_TOKEN` | HCP Terraform API token | Yes | - |
| `TFE_ORG` | Default organization name | Yes | - |
| `TFE_ADDRESS` | TFC/TFE URL | No | `https://app.terraform.io` |

## Workflows

### TFC Operations

#### `watch-run`

Monitor a running plan/apply with live progress and log output.

```bash
terraform_mcp.py watch-run <run-id>
terraform_mcp.py watch-run --workspace <name>  # watches latest run
```

**Behavior:**

- MUST poll `get_run_details` at configurable interval (default: 5s)
- MUST display current status, plan summary, resource counts
- SHOULD stream plan/apply logs as they become available
- MUST exit when run reaches terminal state (applied, errored, discarded, canceled)
- MUST return exit code 0 for success, 1 for failure

**Output:**

```text
Run: run-abc123 | Workspace: my-workspace
Status: planning → planned → applying → applied ✓
Plan: +3 ~1 -0 | Apply: 4/4 resources
Duration: 2m 34s

[Plan Output]
...
```

#### `run-outputs`

View terraform outputs after successful apply.

```bash
terraform_mcp.py run-outputs <run-id>
terraform_mcp.py run-outputs --workspace <name>  # latest successful run
```

**Behavior:**

- MUST retrieve outputs from the specified run or latest successful run
- SHOULD format sensitive outputs as `(sensitive)` unless `--show-sensitive` flag provided

#### `workspace-status`

Overview of workspace(s).

```bash
terraform_mcp.py workspace-status                    # all workspaces (brief)
terraform_mcp.py workspace-status <name>             # single workspace detail
terraform_mcp.py workspace-status --filter "prod-*"  # glob filter
```

**Output includes:**

- Workspace name, ID
- Last run status and timestamp
- Terraform version
- VCS info (if configured)
- Variable count

#### `list-runs`

Recent runs for a workspace.

```bash
terraform_mcp.py list-runs <workspace> [--limit N] [--status STATUS]
```

**Options:**

- `--limit N` - Number of runs (default: 10)
- `--status STATUS` - Filter by status (pending, planning, planned, applying, applied, errored, etc.)

### Documentation Workflows

#### `list-providers`

Discover available providers.

```bash
terraform_mcp.py list-providers                    # popular providers
terraform_mcp.py list-providers --search "cloud"   # search by keyword
terraform_mcp.py list-providers --namespace aws    # by namespace
```

#### `provider-docs`

Look up provider resource/data source documentation.

```bash
terraform_mcp.py provider-docs aws                           # provider overview
terraform_mcp.py provider-docs aws --resource lambda_function  # specific resource
terraform_mcp.py provider-docs aws --data-source ami         # data source
terraform_mcp.py provider-docs aws --list-resources          # list all resources
```

**Behavior:**

- MUST use `search_providers` to find provider doc IDs
- MUST use `get_provider_details` to fetch documentation
- SHOULD return formatted markdown with arguments, attributes, examples

### Discovery Commands

```bash
terraform_mcp.py list-tools              # List available MCP tools
terraform_mcp.py describe <tool_name>    # Describe tool schema
```

## Implementation Details

### Session Management

To avoid ~2s Docker startup overhead per command:

1. First command spawns Docker container, saves PID to `~/.cache/terraform-mcp/`
2. Subsequent commands reuse the running process via stdio
3. Process auto-terminates after 5 minutes idle
4. Script MUST handle stale sessions gracefully (respawn if needed)

```python
SESSION_DIR = Path.home() / ".cache" / "terraform-mcp"
SESSION_TIMEOUT = 300  # 5 minutes

def get_or_create_session() -> subprocess.Popen:
    pid_file = SESSION_DIR / "server.pid"
    if pid_file.exists():
        pid = int(pid_file.read_text())
        if process_alive(pid):
            return reconnect(pid)

    # Spawn new
    proc = subprocess.Popen(
        ["docker", "run", "-i", "--rm",
         "-e", f"TFE_TOKEN={os.environ['TFE_TOKEN']}",
         "-e", f"TFE_ADDRESS={os.environ.get('TFE_ADDRESS', 'https://app.terraform.io')}",
         "hashicorp/terraform-mcp-server:0.3.3"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    pid_file.write_text(str(proc.pid))
    return proc
```

### MCP Client

JSON-RPC 2.0 over stdio:

```python
class MCPStdioClient:
    def __init__(self, proc: subprocess.Popen):
        self.proc = proc
        self.request_id = 0

    def call(self, tool: str, args: dict) -> dict:
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {"name": tool, "arguments": args}
        }
        self.proc.stdin.write(json.dumps(request).encode() + b"\n")
        self.proc.stdin.flush()
        response = json.loads(self.proc.stdout.readline())
        return response.get("result", {})
```

### Direct HCP API Client

For log streaming when MCP doesn't provide full logs:

```python
class HCPTerraformClient:
    def __init__(self, token: str, address: str):
        self.client = httpx.Client(
            base_url=address,
            headers={"Authorization": f"Bearer {token}"}
        )

    def get_plan_logs(self, plan_id: str) -> str:
        """Stream plan logs from HCP Terraform API."""
        resp = self.client.get(f"/api/v2/plans/{plan_id}/logs")
        return resp.text

    def get_apply_logs(self, apply_id: str) -> str:
        """Stream apply logs from HCP Terraform API."""
        resp = self.client.get(f"/api/v2/applies/{apply_id}/logs")
        return resp.text
```

### Output Formatting

```bash
--format yaml    # YAML output (default)
--format json    # Compact JSON
--format compact # Minimal output
--brief          # Essential fields only
```

### Error Handling

- Docker not available → Clear error, suggest install
- TFE_TOKEN missing → Prompt to set environment variable
- TFE_ORG missing → Prompt to set environment variable
- Run not found → Suggest `list-runs` to find valid run IDs
- Network timeout → Retry with exponential backoff for `watch-run`
- Session stale → Respawn Docker process automatically

## File Structure

```text
fzymgc-house/skills/terraform/
├── SKILL.md                    # Skill definition & usage docs
├── scripts/
│   └── terraform_mcp.py        # Gateway script (single file, uv run)
└── references/
    ├── workspaces.md           # Workspace operations reference
    ├── runs.md                 # Run monitoring reference
    └── providers.md            # Provider lookup reference
```

## SKILL.md Outline

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

All operations MUST use: `${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py`

## Quick Reference

| Task | Command |
|------|---------|
| Watch a run | `watch-run <run-id>` |
| Watch latest run | `watch-run --workspace <name>` |
| View run outputs | `run-outputs --workspace <name>` |
| Workspace status | `workspace-status [name]` |
| List runs | `list-runs <workspace>` |
| Provider docs | `provider-docs aws --resource lambda_function` |

## Configuration

The following environment variables MUST be set:

- `TFE_TOKEN` - HCP Terraform API token
- `TFE_ORG` - Default organization name

The following environment variable MAY be set:

- `TFE_ADDRESS` - TFC/TFE URL (default: <https://app.terraform.io>)

## Workflows

[Detailed workflow documentation...]

## Best Practices

- SHOULD use `watch-run --workspace <name>` rather than manually finding run IDs
- SHOULD use `workspace-status` to get an overview before investigating runs
- MUST NOT use raw MCP tools directly; use the provided workflows
```

## Testing Strategy

1. **Unit tests**: Mock MCP responses, verify workflow logic
2. **Integration tests**: Against real TFC organization (with test workspace)
3. **Manual validation**: Run each workflow, verify output quality

## Open Questions

1. Does `get_run_details` include full plan/apply logs, or just metadata?
   - **Mitigation**: Implement direct HCP API fallback

2. Should we support watching multiple runs simultaneously?
   - **Decision**: No, keep simple. User can run multiple terminals.

3. Should we cache provider documentation locally?
   - **Decision**: No for MVP. MCP server may have its own caching.

## Implementation Plan

1. Create directory structure and SKILL.md stub
2. Implement terraform_mcp.py with:
   - MCP stdio client
   - Session management
   - Direct HCP API client (for logs)
3. Implement workflows in order:
   - `workspace-status` (simplest)
   - `list-runs`
   - `watch-run` (most complex)
   - `run-outputs`
   - `provider-docs`
   - `list-providers`
4. Write reference documentation
5. Test against real TFC organization
6. Update CLAUDE.md to reference the skill
