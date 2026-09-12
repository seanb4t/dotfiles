# Beads Integration for PR Review Skills

**Date:** 2026-02-15
**Status:** Draft
**Scope:** `review-pr` and `respond-to-pr-comments` skills

## Problem

The `review-pr` and `respond-to-pr-comments` skills are functionally independent
but logically adjacent. Key issues:

- **Ephemeral data**: review-pr writes findings to a temp dir that's deleted after
  the session. Context is lost between sessions.
- **No shared state**: respond-to-pr-comments starts from scratch each time,
  re-querying GitHub API without knowledge of prior review-pr findings.
- **Duplicate work**: Both skills independently gather PR history and prior comments.
- **No feedback loop**: Re-reviews can't efficiently diff against prior findings.
- **Token waste**: Orchestrator processes every finding twice (agent output + aggregation).

## Solution

Use [beads](https://github.com/steveyegge/beads) as the persistent data layer
between both skills. Subagents create finding beads directly via `bd` CLI.
Beads become the single source of truth for review state across sessions.

## Approach

**Approach B: Subagents create beads directly.** No intermediate JSONL format.

- Orchestrator creates the PR review parent bead and passes its ID to subagents.
- Subagents create child finding beads via `bd create`.
- respond-to-pr-comments queries beads to understand prior review state.
- Re-reviews: subagents query their own prior findings, output deltas.

Chosen over two alternatives:

- **A (orchestrator converts JSONL to beads)**: Every finding processed twice — agent
  formats JSONL, orchestrator re-reads and converts to beads. Token-inefficient.
- **C (JSONL + post-hoc sync script)**: Two sources of truth during session. Extra
  script to maintain. Sync step could be forgotten.

## Data Model

### Hierarchy

```text
Epic (existing project epic, if one exists for this PR)
  └── PR Review bead (one per PR)
        ├── Finding bead (child)
        ├── Finding bead (child)
        └── ...
```

The epic link is optional. If no epic is associated with the PR, the PR review
bead is a top-level bead.

### Labels as Discriminator

Review beads use the project's standard prefix (e.g., `bd-`). Labels distinguish
review beads from regular project issues:

- **PR review parent**: labels `pr-review,pr:<number>`
- **Finding beads**: labels `pr-review-finding,aspect:<name>,severity:<level>,turn:<N>`

All queries filter by label, not by prefix.

### PR Review Bead (Parent)

| Field | Value |
|-------|-------|
| type | `epic` |
| title | `Review: PR #<number> — <pr-title>` |
| external-ref | `https://github.com/{owner}/{repo}/pull/<number>` |
| labels | `pr-review`, `pr:<number>` |
| parent | epic ID (if found), otherwise none |
| description | PR body summary |

### Finding Bead (Child)

| Field | Value |
|-------|-------|
| type | `bug`, `task`, or `feature` (per finding nature) |
| title | Finding description (first sentence) |
| priority | Mapped from severity (see below) |
| labels | `pr-review-finding`, `aspect:<name>`, `severity:<level>`, `turn:<N>` |
| parent | PR review bead ID |
| external-ref | Full URL to PR or specific PR comment |
| description | Full finding details, file location, suggested fix |

### Severity to Priority Mapping

| Severity | Priority | Default Type |
|----------|----------|-------------|
| critical | 0 | bug |
| important | 1 | bug or task |
| suggestion | 2 | task |
| praise | 3 | task (with `praise` label) or skip |

## Revised review-pr Workflow

### Step 1: Determine Scope

Parse `$ARGUMENTS` for PR number and aspects. Gather PR diff and metadata via `gh`.

Check for existing PR review bead:

```bash
bd list --labels "pr-review,pr:123" --json
```

**If found** (re-review): This is turn N+1. Read the bead ID and current turn.

**If not found** (first review): Create the PR review parent bead:

```bash
bd create "Review: PR #123 — <title>" \
  --type epic \
  --labels "pr-review,pr:123,turn:1" \
  --external-ref "https://github.com/{owner}/{repo}/pull/123" \
  --description "<PR body summary>" \
  --parent <epic-id> \
  --silent
```

The `--parent` flag is only included if an epic is found for this PR.

### Steps 2-4: Unchanged

Select applicable agents, choose models (sonnet/opus), load agent prompts from
`references/`. Same logic as current skill.

### Step 5: Launch Subagents

Each subagent receives:

1. The PR review parent bead ID
2. The current turn number
3. Its aspect name

Subagents create finding beads directly:

```bash
bd create "<title>" \
  --parent <parent-bead-id> \
  --type <bug|task|feature> \
  --priority <0-3> \
  --labels "pr-review-finding,aspect:<aspect>,severity:<severity>,turn:<turn>" \
  --external-ref "<pr-url>" \
  --description "<full details, location, suggested fix>" \
  --silent
```

For re-reviews (turn > 1), subagents query their own prior findings:

```bash
bd list --parent <parent-bead-id> --labels "aspect:<aspect>" --status open --json
```

They close resolved findings (`bd update <id> --status closed`) and create new
ones with the current turn number.

**Batching**: Max 3 concurrent subagents per batch. Wait for each batch to
complete before launching the next. Prioritize `security` and `code` in the
first batch.

### Step 6: Aggregate Results

Query beads instead of reading JSONL files:

```bash
bd list --parent <parent-bead-id> --status open --json
```

Group by priority/severity label. Compile summary for the user.

### Step 7: Post Findings

Post a PR comment using the template below. No temp dir cleanup needed.

## Revised respond-to-pr-comments Workflow

### Phase 1: Setup

1. Identify the PR (same as before).
2. Read unacked comments from GitHub via `pr_comments list <pr> --unacked`.
3. **Query beads** for the PR review bead:

   ```bash
   bd list --labels "pr-review,pr:<number>" --json
   ```

   If found, load all child findings:

   ```bash
   bd list --parent <review-bead-id> --json
   ```

   This provides full context from prior review-pr runs without re-deriving
   from PR comment text.

4. **Cross-reference**: Match GitHub PR comments against existing finding beads
   via `external-ref` URLs. Identifies:
   - Comments that align with existing findings (human reviewer flagged same thing)
   - Comments that are new (not captured by review-pr)
   - Findings with no corresponding reviewer comment (bot-only findings)

5. Locate worktree (same).

### Phase 2: Categorize

Step 2a — categorize with bead context. If a PR comment matches an existing
finding bead, link them via `bd dep add <work-bead> --type relates-to <finding-bead>`.

Steps 2b/2c — clarification and plan presentation (unchanged).

### Phase 3: Implement

Sub-agents receive:

- The comment text and file location
- The related finding bead ID (if one exists)
- Category and instructions

After a sub-agent completes a fix:

1. Create a work bead for the fix (if non-trivial):

   ```bash
   bd create "Fix: <description>" \
     --type task \
     --deps "discovered-from:<finding-bead-id>" \
     --silent
   ```

2. Close the related finding bead: `bd update <finding-bead-id> --status closed`
3. Acknowledge the PR comment: `ack <pr> <comment-id>`

**Concurrency**: Max 3 sub-agents per batch.

### Phase 4: Verify

Quality gate sub-agent runs tests/lint/build. Same as before.

### Phase 4.5: Independent Review

The opus review sub-agent queries beads:

```bash
bd list --parent <review-bead-id> --json
```

Validates that closed findings are actually addressed and open ones have
justification. Same PASS/FAIL/SHIP/BLOCK output format.

### Phase 5: Ship

Commit, push, post response comment using the template below.

## GitHub PR Comment Templates

Both skills post lightweight comments that point to beads for detail.

### Detection

HTML comment marker at top: `<!-- pr-review:<bead-id> -->` for review,
`<!-- pr-review:<bead-id>:response -->` for response. Both skills search
for this marker to find prior comments.

### review-pr Comment

```markdown
<!-- pr-review:<bead-id> -->
## [bead-id] — PR Review

`bd list --parent <bead-id> --status open`

N critical · N important · N suggestions

---

### Critical

**Finding title** `<finding-bead-id>`
Up to two lines of summary describing the issue,
its location, and the recommended fix.

**Another finding** `<finding-bead-id>`
Summary lines here.

### Important

**Finding title** `<finding-bead-id>`
Summary.

### Suggestions

**Finding title** `<finding-bead-id>`
Summary.
```

Every finding is listed. Each finding gets a bold title with bead ID, plus
up to 2 lines of summary (max 3 lines total per finding). Grouped by severity.

### respond-to-pr-comments Comment

```markdown
<!-- pr-review:<bead-id>:response -->
## [bead-id] — Review Response

`bd list --parent <bead-id>`

Addressed N/M · N deferred

| Finding | Status |
|---------|--------|
| <bead-id> | Fixed |
| <bead-id> | Fixed |
| <bead-id> | Deferred — reason |
```

## Configuration

### Beads Prerequisites

The target project must have beads initialized (`bd init`). If beads is not
found, the skill warns and stops.

No special prefix or rig configuration required. Review beads use the project's
standard prefix and are distinguished purely by labels.

### allowed-tools Changes

**review-pr** — add:

```yaml
- "Bash(bd create *)"
- "Bash(bd list *)"
- "Bash(bd update *)"
- "Bash(bd show *)"
- "Bash(bd dep *)"
- "Bash(bd query *)"
- "Bash(bd config *)"
```

**respond-to-pr-comments** — add:

```yaml
- "Bash(bd create *)"
- "Bash(bd list *)"
- "Bash(bd update *)"
- "Bash(bd show *)"
- "Bash(bd dep *)"
- "Bash(bd query *)"
- "Bash(bd comments *)"
```

### Subagent Prompt Changes

Each review-pr agent reference file (`references/agent-*.md`) gets its JSONL
output section replaced with a bead output section:

```markdown
## Bead Output

Create a bead for each finding:

bd create "<title>" \
  --parent <PARENT_BEAD_ID> \
  --type <bug|task|feature> \
  --priority <0-3> \
  --labels "pr-review-finding,aspect:<ASPECT>,severity:<SEVERITY>,turn:<TURN>" \
  --external-ref "<PR_URL>" \
  --description "<full details, location, suggested fix>" \
  --silent

For re-reviews (turn > 1), query prior findings first:

bd list --parent <PARENT_BEAD_ID> --labels "aspect:<ASPECT>" --status open --json

Close resolved findings: bd update <id> --status closed
Create new findings with the current turn number.
```

## What Gets Removed

- `$REVIEW_DIR` temp directory and all references to it
- JSONL output convention and schema documentation
- `rm -rf $REVIEW_DIR` cleanup step
- `mktemp` command in step 1

## What Stays

- `pr_comments` script (reading/acking GitHub comments from human reviewers)
- Model routing logic (sonnet/opus per agent)
- 3-agent batch concurrency limit
- All git/gh commands for diff/metadata gathering
- Phase 4 quality gates
- Phase 4.5 independent review (queries beads instead of git diff)

## Re-review Token Savings

On turn N+1:

1. Orchestrator queries existing beads instead of re-gathering full context
2. Subagents query only their aspect's open findings (one `bd list` call)
3. Subagents skip analysis of resolved areas, focus on deltas
4. GitHub comment is a lightweight diff against prior turn, not a full report
5. respond-to-pr-comments has full context from beads without re-parsing
   PR comment text

## Migration

No migration needed. The skills detect whether beads exist for a given PR:

- If beads found: use them (new workflow)
- If not found: create them (first review)

Existing PRs reviewed before this change have no beads — the next review-pr
run creates the initial bead set as if it were turn 1.
