# Pyroscope Profiling Reference

## Table of Contents

- [Profile Types](#profile-types)
- [Labels](#labels)
- [Fetching Profiles](#fetching-profiles)

## Profile Types

### List available profile types

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_pyroscope_profile_types '{"data_source_uid":"..."}'
```

**Profile type format:** `<name>:<sample_type>:<sample_unit>:<period_type>:<period_unit>`

Common types:

- `process_cpu:cpu:nanoseconds:cpu:nanoseconds` - CPU profiling
- `memory:alloc_objects:count:space:bytes` - Memory allocations
- `memory:inuse_objects:count:space:bytes` - Memory in use

Not all profile types are available for every service.

## Labels

### List label names

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_pyroscope_label_names '{"data_source_uid":"..."}'
```

With matchers:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_pyroscope_label_names '{"data_source_uid":"...","matchers":"{service_name=\"api\"}"}'
```

Labels with double underscores (e.g., `__name__`) are internal.

### List label values

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py list_pyroscope_label_values '{"data_source_uid":"...","name":"service_name"}'
```

## Fetching Profiles

### Fetch profile

```bash
${CLAUDE_PLUGIN_ROOT}/skills/grafana/scripts/grafana_mcp.py fetch_pyroscope_profile '{"data_source_uid":"...","profile_type":"process_cpu:cpu:nanoseconds:cpu:nanoseconds","matchers":"{service_name=\"api\"}"}'
```

Optional: `start_rfc_3339`, `end_rfc_3339`, `max_node_depth`

**Returns:** Profile in DOT format (graphviz)

### Max node depth

- Default: 100 (good balance)
- Lower: Smaller profiles, faster, less detail
- Higher/-1: More detail, larger output

## Common Patterns

### Profile a service

1. `list_pyroscope_label_values` with name "service_name" - Find services
2. `list_pyroscope_profile_types` - See available profiles
3. `fetch_pyroscope_profile` with CPU type first
4. Analyze hotspots in DOT output

### Compare time periods

1. Fetch profile for baseline period
2. Fetch profile for problem period
3. Compare function call distributions

### Debug memory issues

1. Use `memory:inuse_objects:count:space:bytes` profile
2. Look for unexpected allocations
3. Check heap growth patterns

## Tool Reference

### list_pyroscope_profile_types

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| data_source_uid | ✅ | string | Pyroscope datasource UID |
| start_rfc_3339 | | string | Default: 1 hour ago |
| end_rfc_3339 | | string | Default: now |

### list_pyroscope_label_names

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| data_source_uid | ✅ | string | |
| matchers | | string | e.g., {service_name="api"} |
| start_rfc_3339 | | string | |
| end_rfc_3339 | | string | |

### list_pyroscope_label_values

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| data_source_uid | ✅ | string | |
| name | ✅ | string | Label name |
| matchers | | string | Label matchers |
| start_rfc_3339 | | string | |
| end_rfc_3339 | | string | |

### fetch_pyroscope_profile

| Param | Required | Type | Notes |
|-------|----------|------|-------|
| data_source_uid | ✅ | string | |
| profile_type | ✅ | string | From list_pyroscope_profile_types |
| matchers | | string | e.g., {service_name="api"} |
| start_rfc_3339 | | string | Default: 1 hour ago |
| end_rfc_3339 | | string | Default: now |
| max_node_depth | | int | Default: 100, -1 for unlimited |
