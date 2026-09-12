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
