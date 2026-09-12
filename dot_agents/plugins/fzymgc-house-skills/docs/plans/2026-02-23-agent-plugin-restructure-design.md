# Agent & Plugin Restructure Design

Split the single `fzymgc-house` plugin into a two-plugin marketplace,
converting skill-based agents into true Claude Code agents with native
worktree isolation.

## Motivation

The primary driver is **worktree isolation** for fix-worker agents in
the address-findings workflow. Secondary benefits include simplified
orchestrator skills, native model routing, and independent agent
upgrades.

## Repository Structure

```text
fzymgc-house-skills/                    # Marketplace root (repo name unchanged)
├── .claude-plugin/
│   └── marketplace.json                # Lists both plugins
├── homelab/                            # Plugin 1: Infrastructure (renamed from fzymgc-house)
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── grafana/
│       ├── terraform/
│       └── skill-qa/
└── pr-review/                          # Plugin 2: PR Review (new)
    ├── .claude-plugin/plugin.json
    ├── agents/                         # True agents
    │   ├── code-reviewer.md
    │   ├── silent-failure-hunter.md
    │   ├── pr-test-analyzer.md
    │   ├── type-design-analyzer.md
    │   ├── comment-analyzer.md
    │   ├── security-auditor.md
    │   ├── api-contract-checker.md
    │   ├── spec-compliance.md
    │   ├── code-simplifier.md
    │   ├── fix-worker.md
    │   ├── review-gate.md
    │   └── verification-runner.md
    ├── skills/
    │   ├── review-pr/SKILL.md          # Thin orchestrator
    │   ├── address-findings/SKILL.md   # Thin orchestrator
    │   └── respond-to-comments/
    │       ├── SKILL.md
    │       └── scripts/pr_comments
    └── hooks/
        └── hooks.json                  # Optional: SubagentStop hooks
```

## Marketplace Configuration

```json
{
  "name": "fzymgc-house-skills",
  "owner": { "name": "Sean Brandt", "email": "..." },
  "plugins": [
    {
      "name": "homelab",
      "description": "Infrastructure skills for homelab cluster (Grafana, Terraform)",
      "source": "./homelab"
    },
    {
      "name": "pr-review",
      "description": "PR review workflow with specialized review agents and automated fix loop",
      "source": "./pr-review"
    }
  ]
}
```

## Agent Definitions

### Conversion Pattern

Each `references/agent-*.md` file becomes a true agent in
`pr-review/agents/` with YAML frontmatter:

```markdown
---
name: <agent-name>
description: <what it does and when invoked>
model: sonnet
isolation: worktree
tools: Read, Grep, Glob, Bash
---

<existing system prompt body, minus H1 header>
```

### Agent Matrix

| Agent                  | Model  | Isolation | Tools                              | Purpose                      |
|------------------------|--------|-----------|-------------------------------------|------------------------------|
| `code-reviewer`        | sonnet | worktree  | Read, Grep, Glob, Bash              | Guidelines, bugs, quality    |
| `silent-failure-hunter` | sonnet | worktree  | Read, Grep, Glob, Bash             | Error handling, catch blocks |
| `pr-test-analyzer`     | sonnet | worktree  | Read, Grep, Glob, Bash              | Test coverage gaps           |
| `type-design-analyzer` | sonnet | worktree  | Read, Grep, Glob, Bash              | Type encapsulation           |
| `comment-analyzer`     | sonnet | worktree  | Read, Grep, Glob, Bash              | Comment accuracy, doc rot    |
| `security-auditor`     | sonnet | worktree  | Read, Grep, Glob, Bash              | OWASP, secrets, auth, IaC   |
| `api-contract-checker` | sonnet | worktree  | Read, Grep, Glob, Bash              | Breaking changes, schemas    |
| `spec-compliance`      | sonnet | worktree  | Read, Grep, Glob, Bash              | Design doc alignment         |
| `code-simplifier`      | sonnet | worktree  | Read, Grep, Glob, Bash              | Clarity, redundancy          |
| `fix-worker`           | sonnet | worktree  | Read, Edit, Write, Grep, Glob, Bash | Implements fixes             |
| `review-gate`          | sonnet | none      | Read, Grep, Glob, Bash              | Validates fixes after merge  |
| `verification-runner`  | sonnet | worktree  | Read, Grep, Glob, Bash              | Runs tests/lint/build        |

- **Model default**: sonnet. Orchestrator overrides to opus via Task
  `model:` parameter for escalation cases (complex security, novel
  architecture, vague specs).
- **Worktree isolation**: All agents except `review-gate` (which reads
  the merged diff on the PR branch, no isolation needed).
- **Tool restriction**: Review agents are read-only + Bash (for bd/git).
  Only `fix-worker` gets Edit/Write.

### Fix-Worker Agent

New agent for address-findings. Receives a single finding and
implements the fix in its isolated worktree.

**Input contract** (passed via Task prompt):

- `FINDING_BEAD_ID` — the bead to fix
- `WORK_BEAD_ID` — work tracking bead
- `FILE_LOCATION` — where the issue is
- `SUGGESTED_FIX` — the reviewer's suggestion

**Output contract** (returned to orchestrator):

```text
STATUS: FIXED | PARTIAL | FAILED
FINDING: <bead-id>
FILES_CHANGED: <file1>, <file2>, ...
DESCRIPTION: <what was done>
WORKTREE_BRANCH: <branch name from worktree>
```

**Constraints:**

- Fix ONLY the specific finding
- Match existing code style
- Do NOT close beads (orchestrator manages lifecycle)
- Do NOT run tests (verification-runner handles that)

### Review-Gate Agent

New agent that validates fixes after merge. Receives the batch of
finding IDs and the git diff, returns PASS/FAIL per finding.

**Output contract:**

```text
<finding-id>: PASS | FAIL: <reason>
```

### Verification-Runner Agent

New agent for Phase 5. Detects project type, runs quality gates
(tests, lint, build). Attempts fixes on failure (max 3 attempts).

**Output contract:**

```text
STATUS: PASS | FAIL
GATES: tests:PASS lint:PASS build:PASS
FAILURES: <details if any>
```

## Communication Boundary

### Agent → Orchestrator Contract

Agents return structured text results. The orchestrator parses these
to drive bead lifecycle and merge decisions. Agents do NOT update
beads — only the orchestrator closes/updates beads.

### Worktree Merge Protocol

After each batch of fix-workers completes, the orchestrator:

1. Collects worktree branches from Task results
2. For each FIXED result, merges in dependency order:

   ```bash
   git merge --no-ff <worktree-branch> -m "fix(<finding-id>): <description>"
   ```

3. Handles merge conflicts:
   - Unresolvable: mark FAILED, add bead comment, re-queue
   - Conflict should be rare due to dep analysis blocking same-file
     findings from running in parallel
4. Cleans up worktrees: `git worktree remove <path>`

### Conflict Mitigation

Phase 2 dependency analysis prevents parallel execution of findings
that touch the same file. Same-file findings are serialized via
`bd dep add`. This means merge conflicts only occur if a fix
unexpectedly touches files outside its declared scope.

## Orchestrator Skill Changes

### review-pr

Shrinks from ~260 lines to ~120 lines. Steps:

1. Parse input (PR number + aspects)
2. Check for existing review epic bead
3. Gather PR context (gh pr diff/view)
4. Select applicable agents (same heuristic table)
5. Model escalation (sets Task `model:` parameter)
6. Create/reuse parent bead
7. Launch agents via Task with `subagent_type: "<name>"`
   - Pass: diff, PARENT_BEAD_ID, TURN, PR_URL, ASPECT
   - Batches of 3 concurrent, security + code first
8. Aggregate findings from beads
9. Present summary grouped by severity
10. Offer to post as PR comment

**Eliminated**: reference file reads, inline prompt construction,
per-agent tool list management.

### address-findings

Shrinks from ~300 lines to ~200 lines. Revised phases:

- **Phase 1: Load** — Find PR, query epic, load findings (no manual
  worktree discovery — workers create their own)
- **Phase 2: Analyze Dependencies** — Same as before, plus explicit
  same-file → sequential rule for merge safety
- **Phase 3: Triage** — Same (auto-fixable vs needs-human)
- **Phase 4: Fix Loop** — Dispatch `fix-worker` agents via Task
  (max 3 concurrent, respecting deps)
- **Phase 4b: Merge Fix Branches** — NEW. Merge worktree branches
  back to PR branch in dep order
- **Phase 4c: Review Gate** — Dispatch `review-gate` agent with
  merged diff. PASS → close beads. FAIL → re-queue (max 2 retries)
- **Phase 5: Verify** — Dispatch `verification-runner` agent
- **Phase 6: Ship** — Commit, push, post summary

## Release & Migration

### Plugin Rename

- `fzymgc-house/` directory → `homelab/`
- Plugin name in plugin.json: `fzymgc-house` → `homelab`
- Skill namespace: `fzymgc-house:grafana` → `homelab:grafana`

### New Plugin

- `pr-review/` directory with `.claude-plugin/plugin.json`
- Plugin name: `pr-review`
- Skills: `pr-review:review-pr`, `pr-review:address-findings`,
  `pr-review:respond-to-comments`

### Release-Please Config

Remove packages:

- `fzymgc-house/skills/review-pr`
- `fzymgc-house/skills/respond-to-pr-comments`
- `fzymgc-house/skills/address-review-findings`

Add packages:

- `pr-review` (plugin root, starts at 1.0.0)
- `pr-review/skills/review-pr` (starts at 1.0.0)
- `pr-review/skills/address-findings` (starts at 1.0.0)
- `pr-review/skills/respond-to-comments` (starts at 1.0.0)

Update root `.` package:

- Extra-files: `fzymgc-house/plugin.json` → `homelab/plugin.json`
- Add extra-file: `pr-review/plugin.json`

### Version Plan

- `homelab` plugin: continues at 0.8.0 (rename counts as minor bump)
- `pr-review` plugin: starts at 1.0.0
- Marketplace root: bumps to 0.8.0

### CLAUDE.md Updates

All skill references updated:

| Old | New |
|-----|-----|
| `fzymgc-house:grafana` | `homelab:grafana` |
| `fzymgc-house:terraform` | `homelab:terraform` |
| `fzymgc-house:review-pr` | `pr-review:review-pr` |
| `fzymgc-house:respond-to-pr-comments` | `pr-review:respond-to-comments` |
| `fzymgc-house:address-review-findings` | `pr-review:address-findings` |

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Approach | Agents + thin orchestrator skills | Max leverage of new agent features while keeping orchestration in skills (agents can't spawn agents) |
| Worktree scope | Workers only, orchestrator in main context | Orchestrator needs bead access and user interaction |
| Plugin split | Two plugins in one marketplace | Clean separation, independent versioning, shared CI |
| Plugin rename | fzymgc-house → homelab | More descriptive, domain-appropriate |
| PR comments | Moves to pr-review plugin | Tightly coupled to review workflow |
| Review gate | New dedicated agent | Clean separation of concerns |
| Fix-worker isolation | worktree per worker | Enables parallel fixes without conflicts |
| Merge protocol | Orchestrator merges after batch | Explicit, dependency-ordered, conflict-aware |
