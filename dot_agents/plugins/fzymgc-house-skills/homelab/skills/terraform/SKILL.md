---
name: terraform
description: |-
  Terraform Cloud operations and registry documentation lookup.
  Watch runs, view plan/apply logs, check workspace status, look up
  provider docs. Invokes Terraform MCP server on-demand without loading
  tool definitions into context.
allowed-tools:
  - "Bash(uv:*)"
  - "Bash(docker:*)"
  - "Bash(${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py:*)"
  - Read
  - Grep
  - Glob
  - Search
metadata:
  author: fzymgc-house
  version: 0.1.0 # x-release-please-version
---

# Terraform Operations

## Prerequisites

You MUST have the following environment variables configured:

- TFE_TOKEN - HCP Terraform API token (create at
  <https://app.terraform.io/app/settings/tokens>)
- TFE_ORG - Default organization name (required for workspace/run
  operations)

You MAY set:

- TFE_ADDRESS - TFC/TFE URL (defaults to
  <https://app.terraform.io>)

**Note:** Provider documentation commands do not require TFE_ORG.

## Gateway Script

All operations MUST use the gateway script:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py
```

**IMPORTANT**: When running the gateway script, you MAY see
errors/stacktraces from `uv` when running in a sandboxed environment. If
you do, you MUST attempt to re-run the command outside the sandbox, if
permitted.

## Common Workflows

### Viewing Run Status and Logs

#### Scenario: A run has completed and you need to see what happened

You MUST use `run-details` for completed runs:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  run-details <run-id>
```

This command:

- MUST be used for runs in terminal states (applied, errored,
  planned_and_finished, discarded)
- Returns formatted logs with ~70% token reduction compared to raw JSON
- Shows error messages with file locations and line numbers
- Displays resource change summary (+add ~change -destroy)
- Includes apply output for successful runs

Expected output structure:

```text
Status: applied
Message: "Update security group rules"

Changes: +2 ~1 -0

Plan Output:
  ✓ Resource changes validated

Apply Output:
  aws_security_group_rule.allow_https: Creating...
  aws_security_group_rule.allow_https: Creation complete
```

Error format when issues occur:

```text
ERROR: Reference to undeclared resource
  File: main.tf:32:20
  Detail: A managed resource "aws_instance" "web" has not been
  declared in the root module.
```

#### Scenario: A run is in progress and you want to monitor it

You MUST use `watch-run` for in-progress runs:

```bash
# Watch specific run
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  watch-run <run-id>

# Watch latest run for a workspace
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  watch-run --workspace <workspace-name>
```

This command:

- MUST be used for runs in non-terminal states (planning, applying,
  pending, etc.)
- Polls status every 5 seconds (configurable with `--interval`)
- Displays status transitions with timestamps
- Shows plan summary when available
- Automatically exits when run reaches terminal state
- Returns exit code 0 for success states, 1 for failure states

You SHOULD NOT use `--logs` flag with `watch-run` for completed runs.
Use `run-details` instead for formatted output.

The command will guide you:

```text
Run run-abc123 is already in 'applied' state.
Use 'run-details run-abc123' for formatted logs.
```

### Listing and Finding Runs

#### Scenario: You need to see recent activity in a workspace

You MUST use `list-runs`:

```bash
# List recent runs (default: 10 most recent)
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  list-runs <workspace-name>

# More results
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  list-runs <workspace-name> --limit 20

# Filter by status
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  list-runs <workspace-name> --status errored
```

This returns:

- Run ID (use with `run-details` or `watch-run`)
- Status (applied, errored, planning, etc.)
- Commit message or trigger reason
- Created timestamp
- Resource change summary (when available)

Common status values:

- `applied` - Successfully completed
- `errored` - Failed during plan or apply
- `planning` - Currently generating plan
- `applying` - Currently applying changes
- `planned_and_finished` - Plan completed, not applied

**Typical workflow:**

1. List runs to find the run ID
2. Use `run-details <run-id>` to view completed run logs
3. Or use `watch-run <run-id>` to monitor in-progress run

### Checking Workspace Status

#### Scenario: You need an overview of workspace health and configuration

You MUST use `workspace-status`:

```bash
# List all workspaces
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  workspace-status

# Detailed view of specific workspace
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  workspace-status <workspace-name>
```

Without a workspace name, this shows:

- All workspace names
- Current status
- Last run state
- Terraform version

With a workspace name, this shows:

- Execution mode (remote, local, agent)
- Working directory
- VCS repository (if connected)
- Latest run ID and status
- Applied run ID (last successful apply)
- Terraform version
- Auto-apply setting

**Use this workflow:**

1. Run `workspace-status` without args to see all workspaces
2. Identify workspace of interest
3. Run `workspace-status <name>` for details
4. Note the latest run ID
5. Use `run-details <run-id>` or `watch-run <run-id>` as appropriate

### Viewing Terraform Outputs

#### Scenario: You need to see the output values from a run

You MUST use `run-outputs`:

```bash
# From specific run
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  run-outputs <run-id>

# From latest successful apply in workspace
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  run-outputs --workspace <workspace-name>
```

This command:

- MUST target a run in `applied` state
- Returns all output values defined in your Terraform configuration
- Shows sensitive outputs as `<sensitive>` (actual values not
  retrieved)
- Returns empty result if no outputs defined

Expected output:

```yaml
vpc_id: vpc-abc123
subnet_ids:
  - subnet-123
  - subnet-456
database_endpoint: <sensitive>
```

### Looking Up Provider Documentation

#### Scenario: You need documentation for a Terraform provider resource

You MUST use `provider-docs`:

```bash
# Provider overview
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  provider-docs <provider-name>

# Specific resource documentation
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  provider-docs <provider-name> --resource <resource-type>

# Data source documentation
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  provider-docs <provider-name> --data-source <data-source-type>

# List all resources for a provider
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  provider-docs <provider-name> --list-resources
```

Examples:

```bash
# AWS Lambda function resource docs
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  provider-docs aws --resource lambda_function

# AWS AMI data source docs
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  provider-docs aws --data-source ami

# See all AWS resources
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  provider-docs aws --list-resources
```

This returns:

- Resource arguments and their types
- Required vs. optional arguments
- Attribute reference (exported values)
- Example usage
- Import instructions

#### Scenario: You need to find a provider

You MUST use `list-providers`:

```bash
# Search by keyword
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  list-providers --search <keyword>

# List by namespace
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  list-providers --namespace <namespace>
```

Examples:

```bash
# Find cloud providers
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  list-providers --search cloud

# All Cloudflare providers
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  list-providers --namespace cloudflare
```

## Output Formats

You MAY specify output format for any command:

```bash
--format yaml      # YAML output (default, most readable)
--format json      # Compact JSON (for parsing)
--format compact   # Minimal output (for quick checks)
```

## Tool Discovery

When you need to understand available MCP tools:

```bash
# List all tools
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  list-tools

# Get tool schema and parameters
${CLAUDE_PLUGIN_ROOT}/skills/terraform/scripts/terraform_mcp.py \
  describe <tool-name>
```

You SHOULD use this when:

- Gateway script doesn't provide needed operation
- You need to understand raw MCP tool parameters
- Debugging gateway script behavior

## Decision Matrix

Use this to determine the correct command:

| Question                | Command                      | Notes             |
|-------------------------|------------------------------|-------------------|
| Is the run complete?    | `run-details <run-id>`       | Formatted logs    |
| Is the run in progress? | `watch-run <run-id>`         | Live monitoring   |
| Which workspace?        | `workspace-status`           | Overview of all   |
| Recent runs?            | `list-runs <workspace>`      | Get run IDs       |
| What are the outputs?   | `run-outputs <run-id>`       | Applied runs only |
| Need provider docs?     | `provider-docs <provider>`   | Resource docs     |
| Find a provider?        | `list-providers --search`    | Discover          |

## Best Practices

You MUST:

- Use `run-details` for completed runs instead of `watch-run --logs`
- Check `workspace-status` before investigating runs
- Use `list-runs` to find run IDs, not guess them

You SHOULD:

- Use `--workspace` flag with `watch-run` to monitor latest run
- Set reasonable `--limit` values for `list-runs` (default 10 is
  usually sufficient)
- Use `--format compact` for quick status checks

You SHOULD NOT:

- Use raw MCP tools directly when gateway commands exist
- Request logs for in-progress runs (wait for completion)
- Use `watch-run --logs` for runs already in terminal state

## Domain References

Load these only when you need detailed implementation information:

- [workspaces.md](references/workspaces.md) - Workspace management
  implementation
- [runs.md](references/runs.md) - Run state machine and lifecycle
- [providers.md](references/providers.md) - Provider documentation
  lookup implementation
