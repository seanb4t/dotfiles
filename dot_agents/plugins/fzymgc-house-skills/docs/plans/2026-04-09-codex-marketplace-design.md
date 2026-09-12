# Codex Marketplace Compatibility Design

Add a repo-local Codex marketplace layer that exposes the existing Claude
plugin content without forking the actual skills.

## Goal

Make the existing `homelab`, `pr-review`, `jj`, and `superpowers`
plugins installable and discoverable in Codex while keeping the current
Claude marketplace structure intact.

## Constraints

- Claude remains a first-class target. Existing `.claude-plugin`
  manifests and paths stay unchanged.
- Skill content should remain single-source. Codex wrappers should point
  at the current plugin directories instead of duplicating SKILL.md
  trees.
- Codex does not currently support Claude-style named plugin agents.
  Workflows that rely on agent dispatch must keep their existing prompt
  files accessible and document the Codex workaround.
- The new layer should be testable in CI so marketplace drift is caught
  before release.

## Structure

Add a Codex marketplace manifest at `.agents/plugins/marketplace.json`
and create repo-local wrappers under `plugins/`:

```text
.agents/plugins/marketplace.json
plugins/
  homelab/
    .codex-plugin/plugin.json
    skills -> ../../homelab/skills
    .mcp.json -> ../../.mcp.json
  pr-review/
    .codex-plugin/plugin.json
    skills -> ../../pr-review/skills
    agents -> ../../pr-review/agents
    references -> ../../pr-review/references
  jj/
    .codex-plugin/plugin.json
    skills -> ../../jj/skills
    hooks -> ../../jj/hooks
    commands -> ../../jj/commands
  superpowers/
    .codex-plugin/plugin.json
    skills -> ../../superpowers/skills
    agents -> ../../superpowers/agents
    hooks -> ../../superpowers/hooks
    references -> ../../superpowers/references
    scripts -> ../../superpowers/scripts
    commands -> ../../superpowers/commands
```

The wrappers are intentionally thin. Their job is to satisfy Codex's
plugin discovery rules and provide stable relative paths for the actual
skill assets.

## Manifest Strategy

Each Codex plugin manifest will include:

- real `name`, `version`, and `description`
- `skills` pointing at the wrapper's symlinked `skills/`
- optional `hooks` and `mcpServers` where those components exist
- repository metadata shared across plugins
- concise `interface` metadata so the plugins render cleanly in Codex

The marketplace manifest will list the four plugins in the same order as
the Claude marketplace and mark them `AVAILABLE` with
`authentication: ON_INSTALL`.

## Compatibility Notes

### Skill reuse

Codex can load the same SKILL.md content that Claude uses, so most
skills require no body changes.

### Agent-dispatch workflows

`pr-review` and parts of `superpowers` refer to Claude's named `Task`
subagents. Codex cannot install those agent definitions natively today.
The existing guidance in
`superpowers/skills/using-superpowers/references/codex-tools.md`
already defines the workaround: load the relevant prompt file and
dispatch a generic `spawn_agent` worker with that prompt body. The new
Codex wrapper must expose the referenced `agents/` directories so that
workflow remains usable.

## Verification

Add a pytest regression test that verifies:

- the Codex marketplace file exists and contains the expected plugin set
- each marketplace entry points to an existing plugin wrapper
- each wrapper contains a `.codex-plugin/plugin.json`
- each manifest's declared component paths exist

Extend CI's existing pytest job to run the new test alongside the hook
tests.

## Rollout

This change is additive. Users who want Codex support can point Codex at
the repo-local marketplace, while Claude users continue to install the
existing marketplace as before.
