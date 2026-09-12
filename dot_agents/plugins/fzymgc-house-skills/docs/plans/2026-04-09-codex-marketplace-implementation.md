# Codex Marketplace Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repo-local Codex marketplace and plugin wrappers for the existing Claude plugin content without duplicating the skills.

**Architecture:** Keep the existing Claude plugin directories as the source of
truth. Add `plugins/<name>/` wrappers with `.codex-plugin/plugin.json`
manifests and symlink their component directories back to the current plugin
roots. Add a repo-local Codex marketplace manifest that points to those
wrappers, then verify the structure with pytest and CI.

**Tech Stack:** JSON manifests, Markdown docs, symlinks, pytest, GitHub Actions

**Design doc:** `docs/plans/2026-04-09-codex-marketplace-design.md`

---

## Task 1: Add Codex marketplace regression coverage

**Files:**

- Create: `tests/test_codex_marketplace.py`

- Modify: `.github/workflows/check-skills.yml`

- [ ] **Step 1: Write the failing test**

Create a pytest that loads `.agents/plugins/marketplace.json`, asserts
the expected plugin names, and checks that each wrapper manifest and
declared path exists.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest tests/test_codex_marketplace.py -v --import-mode=importlib`
Expected: FAIL because `.agents/plugins/marketplace.json` and the
wrapper manifests do not exist yet.

- [ ] **Step 3: Update CI to include the new test file**

Modify the existing pytest job so it runs:
`uv run --with pytest pytest .claude/hooks/tests/ jj/hooks/tests/ tests/ -v --import-mode=importlib`

- [ ] **Step 4: Commit**

Commit using VCS-appropriate commands per `superpowers/references/vcs-preamble.md`.

## Task 2: Scaffold Codex marketplace wrappers

**Files:**

- Create: `.agents/plugins/marketplace.json`

- Create: `plugins/homelab/.codex-plugin/plugin.json`

- Create: `plugins/pr-review/.codex-plugin/plugin.json`

- Create: `plugins/jj/.codex-plugin/plugin.json`

- Create: `plugins/superpowers/.codex-plugin/plugin.json`

- Create: `plugins/homelab/skills` (symlink)

- Create: `plugins/homelab/.mcp.json` (symlink)

- Create: `plugins/pr-review/skills` (symlink)

- Create: `plugins/pr-review/agents` (symlink)

- Create: `plugins/pr-review/references` (symlink)

- Create: `plugins/jj/skills` (symlink)

- Create: `plugins/jj/hooks` (symlink)

- Create: `plugins/jj/commands` (symlink)

- Create: `plugins/superpowers/skills` (symlink)

- Create: `plugins/superpowers/agents` (symlink)

- Create: `plugins/superpowers/hooks` (symlink)

- Create: `plugins/superpowers/references` (symlink)

- Create: `plugins/superpowers/scripts` (symlink)

- Create: `plugins/superpowers/commands` (symlink)

- [ ] **Step 1: Add the marketplace manifest**

Write `.agents/plugins/marketplace.json` with four entries:
`homelab`, `pr-review`, `jj`, and `superpowers`, each pointing to
`./plugins/<name>` with `policy.installation: AVAILABLE` and
`policy.authentication: ON_INSTALL`.

- [ ] **Step 2: Add plugin manifests**

Write `.codex-plugin/plugin.json` for each wrapper with real metadata,
`skills: "./skills/"`, and optional `hooks` or `mcpServers` where those
components exist.

- [ ] **Step 3: Create wrapper symlinks**

Link each wrapper back to the existing plugin directories so the skill
content stays single-source.

- [ ] **Step 4: Run the new test to verify it passes**

Run: `uv run --with pytest pytest tests/test_codex_marketplace.py -v --import-mode=importlib`
Expected: PASS

- [ ] **Step 5: Commit**

Commit using VCS-appropriate commands per `superpowers/references/vcs-preamble.md`.

## Task 3: Document the Codex installation path

**Files:**

- Modify: `README.md`

- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the public README**

Document that the repo now contains a Codex marketplace at
`.agents/plugins/marketplace.json`, explain that the `plugins/`
directory contains thin Codex wrappers, and note the current agent
dispatch limitation for `pr-review` and `superpowers`.

- [ ] **Step 2: Update repo-maintainer guidance**

Add Codex wrapper structure to `CLAUDE.md` so future edits keep the
Claude and Codex manifests in sync.

- [ ] **Step 3: Run markdown lint**

Run: `rumdl check README.md CLAUDE.md docs/plans/2026-04-09-codex-marketplace-design.md docs/plans/2026-04-09-codex-marketplace-implementation.md`
Expected: PASS

- [ ] **Step 4: Commit**

Commit using VCS-appropriate commands per `superpowers/references/vcs-preamble.md`.
