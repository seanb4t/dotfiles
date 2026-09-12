# Agent & Plugin Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the single fzymgc-house plugin into a two-plugin marketplace (homelab + pr-review),
converting skill-based review agents into true Claude Code agents with native worktree isolation.

**Architecture:** Marketplace repo hosts two plugins. Infrastructure skills (grafana, terraform, skill-qa) stay
in the renamed `homelab` plugin. PR review workflow (review-pr, address-findings, respond-to-comments) moves to a
new `pr-review` plugin with 12 true agents in `agents/`. Orchestrator skills become thin dispatchers.

**Tech Stack:** Claude Code plugin system (agents, skills, hooks), beads CLI, release-please, lefthook, rumdl

**Design doc:** `docs/plans/2026-02-23-agent-plugin-restructure-design.md`

---

## Task 1: Rename fzymgc-house → homelab (directory + configs)

### Files

- Rename: `fzymgc-house/` → `homelab/`
- Modify: `homelab/.claude-plugin/plugin.json` (name field)
- Modify: `.claude-plugin/marketplace.json` (plugin entry)
- Modify: `release-please-config.json` (package paths)
- Modify: `.release-please-manifest.json` (package paths)
- Modify: `CLAUDE.md` (skill references)

### Step 1: Rename the directory

```bash
git mv fzymgc-house homelab
```

### Step 2: Update homelab plugin.json

Change `name` from `fzymgc-house` to `homelab` in `homelab/.claude-plugin/plugin.json`.
Keep the current version (`0.7.0`).

```json
{
  "name": "homelab",
  "version": "0.7.0",
  "description": "Infrastructure skills for homelab cluster (Grafana, Terraform)"
}
```

### Step 3: Update marketplace.json

Update the existing plugin entry's `name`, `description`, and `source` path.
Do NOT add the pr-review plugin yet (that's Task 3).

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "fzymgc-house-skills",
  "version": "0.7.0",
  "description": "Skills for use with fzymgc-house self-hosted cluster",
  "owner": {
    "name": "Sean Brandt",
    "email": "4678+seanb4t@users.noreply.github.com"
  },
  "plugins": [
    {
      "name": "homelab",
      "description": "Infrastructure skills for homelab cluster (Grafana, Terraform)",
      "source": "./homelab"
    }
  ]
}
```

### Step 4: Update release-please-config.json

Replace all `fzymgc-house/` paths with `homelab/`. The three infra skills stay. Remove the three
PR-review skill packages (they move in Task 3). Update the root `.` package extra-files.

Packages to keep (with renamed paths):

- `.` (root) — update extra-files to `homelab/plugin.json`
- `homelab/skills/grafana`
- `homelab/skills/terraform`
- `homelab/skills/skill-qa`

Packages to remove:

- `fzymgc-house/skills/review-pr`
- `fzymgc-house/skills/respond-to-pr-comments`
- `fzymgc-house/skills/address-review-findings`

### Step 5: Update .release-please-manifest.json

Same renames. Remove the three PR-review entries. Keep versions as-is for renamed paths.

```json
{
  ".": "0.7.0",
  "homelab/skills/grafana": "0.2.0",
  "homelab/skills/terraform": "0.2.0",
  "homelab/skills/skill-qa": "0.2.0"
}
```

### Step 6: Update CLAUDE.md

Replace all `fzymgc-house:` skill references with `homelab:` for the three infra skills.
Leave the PR-review references for now (Task 8 updates those).

### Step 7: Commit

```bash
git add -A && git commit -m "feat!: rename fzymgc-house plugin to homelab

BREAKING CHANGE: Plugin name changed from fzymgc-house to homelab.
Skill invocations change: fzymgc-house:grafana → homelab:grafana, etc."
```

---

## Task 2: Update CI workflows for multi-plugin structure

### Files

- Modify: `.github/workflows/check-skills.yml`

### Step 1: Update drift-check to scan both plugin dirs

The current CI hardcodes `fzymgc-house/skills`. Update to scan both `homelab/skills` and
`pr-review/skills` (pr-review doesn't exist yet, so use a glob that handles both).

```yaml
name: Check Skills

on:
  pull_request:
    branches: [main]

jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check release-please config covers all skills
        run: |
          actual=$(find homelab/skills pr-review/skills -name SKILL.md -exec dirname {} \; 2>/dev/null | sort)
          configured=$(jq -r '.packages | keys[] | select(. != "." and (. | test("/skills/")))' release-please-config.json | sort)
          if ! diff <(echo "$actual") <(echo "$configured"); then
            echo "::error::Skill directories and release-please-config.json are out of sync"
            exit 1
          fi

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install rumdl
        run: |
          tag=$(gh release view --repo rvben/rumdl --json tagName -q .tagName)
          gh release download "$tag" --repo rvben/rumdl \
            --pattern "rumdl-${tag}-x86_64-unknown-linux-gnu.tar.gz" --output - \
            | tar xz -C /usr/local/bin rumdl
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Lint markdown
        run: |
          rumdl check homelab/skills/*/SKILL.md
          rumdl check pr-review/skills/*/SKILL.md
          rumdl check pr-review/agents/*.md
```

### Step 2: Commit

```bash
git add .github/workflows/check-skills.yml
git commit -m "ci: update workflows for multi-plugin marketplace structure"
```

---

## Task 3: Create pr-review plugin scaffold

### Files

- Create: `pr-review/.claude-plugin/plugin.json`
- Create: `pr-review/agents/` (empty directory, placeholder)
- Create: `pr-review/skills/` (empty directory, placeholder)
- Modify: `.claude-plugin/marketplace.json` (add pr-review plugin)
- Modify: `release-please-config.json` (add pr-review packages)
- Modify: `.release-please-manifest.json` (add pr-review versions)

### Step 1: Create plugin manifest

```bash
mkdir -p pr-review/.claude-plugin pr-review/agents pr-review/skills
```

Write `pr-review/.claude-plugin/plugin.json`:

```json
{
  "name": "pr-review",
  "version": "1.0.0",
  "description": "PR review workflow with specialized review agents and automated fix loop"
}
```

### Step 2: Add pr-review to marketplace.json

Add the second plugin entry to the `plugins` array:

```json
{
  "name": "pr-review",
  "description": "PR review workflow with specialized review agents and automated fix loop",
  "source": "./pr-review"
}
```

### Step 3: Add pr-review packages to release-please-config.json

Add these packages:

```json
"pr-review": {
  "release-type": "simple",
  "package-name": "pr-review",
  "extra-files": [
    {
      "type": "json",
      "path": "pr-review/.claude-plugin/plugin.json",
      "jsonpath": "$.version"
    }
  ]
},
"pr-review/skills/review-pr": {
  "release-type": "simple",
  "package-name": "review-pr",
  "extra-files": [
    {
      "type": "generic",
      "path": "pr-review/skills/review-pr/SKILL.md"
    }
  ]
},
"pr-review/skills/address-findings": {
  "release-type": "simple",
  "package-name": "address-findings",
  "extra-files": [
    {
      "type": "generic",
      "path": "pr-review/skills/address-findings/SKILL.md"
    }
  ]
},
"pr-review/skills/respond-to-comments": {
  "release-type": "simple",
  "package-name": "respond-to-comments",
  "extra-files": [
    {
      "type": "generic",
      "path": "pr-review/skills/respond-to-comments/SKILL.md"
    }
  ]
}
```

### Step 4: Add pr-review to .release-please-manifest.json

```json
"pr-review": "1.0.0",
"pr-review/skills/review-pr": "1.0.0",
"pr-review/skills/address-findings": "1.0.0",
"pr-review/skills/respond-to-comments": "1.0.0"
```

### Step 5: Commit

```bash
git add pr-review/ .claude-plugin/marketplace.json release-please-config.json .release-please-manifest.json
git commit -m "feat: scaffold pr-review plugin with marketplace entry"
```

---

## Task 4: Convert 9 review agent references to true agents

### Files

- Create: `pr-review/agents/code-reviewer.md`
- Create: `pr-review/agents/silent-failure-hunter.md`
- Create: `pr-review/agents/pr-test-analyzer.md`
- Create: `pr-review/agents/type-design-analyzer.md`
- Create: `pr-review/agents/comment-analyzer.md`
- Create: `pr-review/agents/security-auditor.md`
- Create: `pr-review/agents/api-contract-checker.md`
- Create: `pr-review/agents/spec-compliance.md`
- Create: `pr-review/agents/code-simplifier.md`
- Source: `homelab/skills/review-pr/references/agent-*.md` (9 files)

### Step 1: Convert each agent

For each of the 9 files in `homelab/skills/review-pr/references/agent-*.md`:

1. Read the source file
2. Remove the `# Title` H1 header line
3. Prepend YAML frontmatter with:
   - `name:` derived from filename (e.g., `agent-code-reviewer.md` → `code-reviewer`)
   - `description:` one-line summary of what the agent does + "Used by the review-pr
     orchestrator for the `<aspect>` aspect."
   - `model: sonnet`
   - `isolation: worktree`
   - `tools: Read, Grep, Glob, Bash`
4. Write to `pr-review/agents/<name>.md`

Agent name → aspect mapping:

- `code-reviewer` → `code`
- `silent-failure-hunter` → `errors`
- `pr-test-analyzer` → `tests`
- `type-design-analyzer` → `types`
- `comment-analyzer` → `comments`
- `security-auditor` → `security`
- `api-contract-checker` → `api`
- `spec-compliance` → `spec`
- `code-simplifier` → `simplify`

Example frontmatter for code-reviewer:

```yaml
---
name: code-reviewer
description: >-
  Reviews code for project guideline compliance, bugs, and quality issues.
  Used by the review-pr orchestrator for the `code` aspect.
model: sonnet
isolation: worktree
tools: Read, Grep, Glob, Bash
---
```

### Step 2: Verify all 9 agents created

```bash
ls pr-review/agents/*.md | wc -l
# Expected: 9
```

### Step 3: Commit

```bash
git add pr-review/agents/
git commit -m "feat(pr-review): convert 9 review agent references to true agents

Each agent gets YAML frontmatter with model: sonnet, isolation: worktree,
and read-only tool access. System prompts preserved from original references."
```

---

## Task 5: Create 3 new agents (fix-worker, review-gate, verification-runner)

### Files

- Create: `pr-review/agents/fix-worker.md`
- Create: `pr-review/agents/review-gate.md`
- Create: `pr-review/agents/verification-runner.md`

### Step 1: Write fix-worker agent

Write `pr-review/agents/fix-worker.md` per the design doc's Fix-Worker Agent section.
Key details:

- `tools: Read, Edit, Write, Grep, Glob, Bash` (this is the only agent with Edit/Write)
- `isolation: worktree`
- Input/output contracts from design doc
- Constraints: fix only the specific finding, don't close beads, don't run tests

### Step 2: Write review-gate agent

Write `pr-review/agents/review-gate.md`:

- `tools: Read, Grep, Glob, Bash` (read-only)
- NO `isolation` field (runs on the PR branch directly)
- Receives batch of finding IDs + git diff
- Returns PASS/FAIL per finding

### Step 3: Write verification-runner agent

Write `pr-review/agents/verification-runner.md`:

- `tools: Read, Grep, Glob, Bash`
- `isolation: worktree`
- Detects project type, runs quality gates
- Max 3 retry attempts on failure
- Returns STATUS + per-gate results

### Step 4: Verify all 12 agents

```bash
ls pr-review/agents/*.md | wc -l
# Expected: 12
```

### Step 5: Commit

```bash
git add pr-review/agents/
git commit -m "feat(pr-review): add fix-worker, review-gate, and verification-runner agents

New agents for the address-findings workflow:
- fix-worker: implements fixes in isolated worktrees
- review-gate: validates fixes after merge (no isolation)
- verification-runner: runs quality gates (tests/lint/build)"
```

---

## Task 6: Move and rewrite review-pr skill as thin orchestrator

### Files

- Create: `pr-review/skills/review-pr/SKILL.md`
- Source: `homelab/skills/review-pr/SKILL.md` (current orchestrator)
- Delete later: `homelab/skills/review-pr/` (entire directory, Task 9)

### Step 1: Write the new thin orchestrator

Create `pr-review/skills/review-pr/SKILL.md`. The skill keeps the same frontmatter `name`,
`description`, and `argument-hint` but:

- `allowed-tools`: same git/gh/bd Bash patterns, plus `Task`
- **Remove** `Read` from allowed-tools (no longer reads reference files)
- Body: ~120 lines covering the 10 steps from the design doc

Key differences from current skill:

- **No Step 4 "Load Agent Prompts"** — agents have their own prompts
- **Step 7** uses `subagent_type: "<agent-name>"` instead of constructing inline Task prompts
- **No per-agent tool lists** — agents define their own
- Model escalation just sets `model:` parameter on Task call

Preserve:

- Same aspect selection heuristics (always: code, security; conditional: tests, errors, etc.)
- Same model escalation decision tree
- Same bead creation/query patterns
- Same batching (max 3 concurrent, security + code first)
- Same summary format and PR comment template

### Step 2: Lint the new skill

```bash
rumdl check pr-review/skills/review-pr/SKILL.md
```

### Step 3: Commit

```bash
git add pr-review/skills/review-pr/
git commit -m "feat(pr-review): rewrite review-pr as thin orchestrator skill

Dispatches to named agents instead of reading reference files and
constructing inline prompts. Agents define their own system prompts,
tools, and default models. ~120 lines down from ~260."
```

---

## Task 7: Move and rewrite address-findings skill as thin orchestrator

### Files

- Create: `pr-review/skills/address-findings/SKILL.md`
- Copy: `homelab/skills/address-review-findings/references/bd-reference.md` →
  `pr-review/skills/address-findings/references/bd-reference.md`
- Source: `homelab/skills/address-review-findings/SKILL.md`
- Delete later: `homelab/skills/address-review-findings/` (Task 9)

### Step 1: Copy bd-reference.md

```bash
mkdir -p pr-review/skills/address-findings/references
cp homelab/skills/address-review-findings/references/bd-reference.md \
   pr-review/skills/address-findings/references/bd-reference.md
```

### Step 2: Write the new thin orchestrator

Create `pr-review/skills/address-findings/SKILL.md`. ~200 lines. Key changes from current:

- **Phase 1: Load** — No manual worktree discovery. Workers create their own worktrees.
- **Phase 2: Analyze Dependencies** — Same, plus explicit same-file → sequential rule
- **Phase 3: Triage** — Same (auto-fixable vs needs-human)
- **Phase 4: Fix Loop** — Dispatch `fix-worker` agents via `Task(subagent_type: "fix-worker")`.
  Max 3 concurrent, respecting deps. No inline fix prompts.
- **Phase 4b: Merge Fix Branches** — NEW. Collect WORKTREE_BRANCH from Task results.
  Merge in dependency order. Handle conflicts. Clean up worktrees.
- **Phase 4c: Review Gate** — Dispatch `review-gate` agent with merged diff + finding IDs.
  Parse PASS/FAIL results. Close beads on PASS, re-queue on FAIL (max 2 retries).
- **Phase 5: Verify** — Dispatch `verification-runner` agent.
- **Phase 6: Ship** — Same (commit, push, post summary).

Update frontmatter:

- `name: address-findings` (shortened from `address-review-findings`)
- Same `description` and `argument-hint`
- `allowed-tools`: same patterns but no Read (agents read their own files)

### Step 3: Lint

```bash
rumdl check pr-review/skills/address-findings/SKILL.md
```

### Step 4: Commit

```bash
git add pr-review/skills/address-findings/
git commit -m "feat(pr-review): rewrite address-findings as thin orchestrator

New phases 4b (merge fix branches) and 4c (review gate) for worktree
merge protocol. Fix-workers and verification-runner are now true agents
with worktree isolation."
```

---

## Task 8: Move respond-to-comments skill

### Files

- Create: `pr-review/skills/respond-to-comments/SKILL.md`
- Create: `pr-review/skills/respond-to-comments/scripts/pr_comments`
- Copy: `homelab/skills/respond-to-pr-comments/references/DESIGN.md` →
  `pr-review/skills/respond-to-comments/references/DESIGN.md`
- Source: `homelab/skills/respond-to-pr-comments/`
- Delete later: `homelab/skills/respond-to-pr-comments/` (Task 9)

### Step 1: Copy the skill directory

```bash
mkdir -p pr-review/skills/respond-to-comments/scripts
mkdir -p pr-review/skills/respond-to-comments/references
cp homelab/skills/respond-to-pr-comments/SKILL.md \
   pr-review/skills/respond-to-comments/SKILL.md
cp homelab/skills/respond-to-pr-comments/scripts/pr_comments \
   pr-review/skills/respond-to-comments/scripts/pr_comments
cp homelab/skills/respond-to-pr-comments/references/DESIGN.md \
   pr-review/skills/respond-to-comments/references/DESIGN.md
```

### Step 2: Update SKILL.md frontmatter

Change `name:` from `respond-to-pr-comments` to `respond-to-comments`. Update `allowed-tools`
paths to use the new `$CLAUDE_PLUGIN_ROOT` base (the plugin root is now `pr-review/`, so
`$CLAUDE_PLUGIN_ROOT/skills/respond-to-comments/scripts/pr_comments`).

### Step 3: Update CLAUDE.md references

Replace remaining `fzymgc-house:` references for the PR-review skills:

- `fzymgc-house:review-pr` → `pr-review:review-pr`
- `fzymgc-house:respond-to-pr-comments` → `pr-review:respond-to-comments`
- `fzymgc-house:address-review-findings` → `pr-review:address-findings`

### Step 4: Commit

```bash
git add pr-review/skills/respond-to-comments/ CLAUDE.md
git commit -m "feat(pr-review): move respond-to-comments skill from homelab

Skill renamed from respond-to-pr-comments to respond-to-comments.
CLAUDE.md references updated for all pr-review skills."
```

---

## Task 9: Remove old PR-review skills from homelab

### Files

- Delete: `homelab/skills/review-pr/` (entire directory)
- Delete: `homelab/skills/address-review-findings/` (entire directory)
- Delete: `homelab/skills/respond-to-pr-comments/` (entire directory)

### Step 1: Remove the directories

```bash
git rm -r homelab/skills/review-pr
git rm -r homelab/skills/address-review-findings
git rm -r homelab/skills/respond-to-pr-comments
```

### Step 2: Verify homelab only has infra skills

```bash
ls homelab/skills/
# Expected: grafana  skill-qa  terraform
```

### Step 3: Commit

```bash
git commit -m "feat!: remove PR-review skills from homelab plugin

BREAKING CHANGE: review-pr, address-review-findings, and
respond-to-pr-comments moved to the pr-review plugin."
```

---

## Task 10: Update project CLAUDE.md with new structure

### Files

- Modify: `CLAUDE.md`

### Step 1: Update the Available Skills section

Replace the skills list to reflect the two-plugin structure:

#### homelab plugin

- grafana
- terraform
- skill-qa

#### pr-review plugin

- review-pr
- address-findings
- respond-to-comments

### Step 2: Update the Structure section

Update the directory tree to show both `homelab/` and `pr-review/` with the `agents/` directory.

### Step 3: Update any remaining fzymgc-house references

Search for any remaining `fzymgc-house` references in CLAUDE.md and update them.

### Step 4: Commit

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for two-plugin marketplace structure"
```

---

## Task 11: Validate plugin structure

### Step 1: Run plugin validation

```bash
claude plugin validate .
```

Expected: both plugins discovered, no errors.

### Step 2: Run lint on all markdown

```bash
rumdl check homelab/skills/*/SKILL.md
rumdl check pr-review/skills/*/SKILL.md
rumdl check pr-review/agents/*.md
```

### Step 3: Verify release-please config is in sync

```bash
# Check that every SKILL.md directory has a release-please package
actual=$(find homelab/skills pr-review/skills -name SKILL.md -exec dirname {} \; | sort)
configured=$(jq -r '.packages | keys[] | select(. != "." and (. | test("/skills/")))' release-please-config.json | sort)
diff <(echo "$actual") <(echo "$configured")
```

### Step 4: Verify agent count

```bash
ls pr-review/agents/*.md | wc -l
# Expected: 12
```

### Step 5: Fix any issues found, commit if needed

```bash
git add -A && git commit -m "fix: address validation issues from plugin restructure"
```

---

## Task 12: Update auto-memory

### Files

- Modify:
  `/Users/sean/.claude/projects/-Volumes-Code-github-com-fzymgc-house-fzymgc-house-skills/memory/MEMORY.md`

### Step 1: Update memory with new structure

Add notes about:

- Two-plugin marketplace: `homelab` (infra) + `pr-review` (review workflow)
- Plugin agents live in `pr-review/agents/`, not `references/`
- Skill namespaces: `homelab:grafana`, `pr-review:review-pr`, etc.
- Fix-worker agents use `isolation: worktree`, orchestrator merges branches back

### Step 2: No commit needed (memory is outside repo)

---

## Dependency Graph

```text
Task 1 (rename) ──→ Task 2 (CI) ──→ Task 3 (scaffold) ──→ Task 4 (convert 9 agents)
                                                        ├──→ Task 5 (3 new agents)
                                                        ├──→ Task 6 (review-pr skill)
                                                        ├──→ Task 7 (address-findings skill)
                                                        └──→ Task 8 (respond-to-comments)
                                                                      ↓
                                                              Task 9 (delete old) ──→ Task 10 (CLAUDE.md)
                                                                                  ──→ Task 11 (validate)
                                                                                  ──→ Task 12 (memory)
```

Tasks 4, 5, 6, 7, 8 can run in parallel after Task 3 completes.
Tasks 9, 10, 11, 12 can run in parallel after Tasks 4-8 all complete.
