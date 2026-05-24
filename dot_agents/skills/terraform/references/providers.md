# Provider Documentation Reference

## Provider Namespaces

Common provider namespaces (this is a subset - many more exist in the registry):

| Provider | Namespace |
|----------|-----------|
| aws, azurerm, google, kubernetes, helm, vault | hashicorp |
| cloudflare | cloudflare |
| datadog | DataDog |
| github | integrations |

For providers not listed here, the script defaults to "hashicorp" namespace. Use
`--namespace` flag to specify a different namespace if needed.

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
