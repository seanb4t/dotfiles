# Address Review Findings Skill Design

**Date:** 2026-02-16
**Status:** Draft
**Scope:** New `address-review-findings` skill

## Problem

The `respond-to-pr-comments` skill handles two distinct concerns:

1. Parsing and responding to arbitrary human PR review comments
2. Processing structured findings from the `review-pr` skill (stored as beads)

With the beads integration (2026-02-15), review-pr findings are fully
persisted as beads with labels, dependencies, and descriptions. Processing
these findings is a self-contained workflow that doesn't require GitHub
comment parsing, cross-referencing, or review history gathering.

Mixing these concerns makes respond-to-pr-comments more complex than needed
for the common case: "review-pr found issues, go fix them."

## Solution

Create a new `address-review-findings` skill focused exclusively on
processing beads from a review-pr run. Keep `respond-to-pr-comments` for
handling arbitrary human PR review comments.

Over time, `respond-to-pr-comments` may become a meta-skill that delegates
to `address-review-findings` when a review epic exists.

## Data Model

Uses the hierarchy established by the beads integration design:

```text
Epic (project epic, if one exists for this PR)
  +-- PR Review epic bead (type: epic, created by review-pr)
        +-- Finding bead (child, created by review-pr subagents)
        +-- Finding bead (child)
        +-- Work bead (child, created by this skill for non-trivial fixes)
        +-- ...
```

**Finding beads** (input, created by review-pr):

| Field | Value |
|-------|-------|
| type | `bug`, `task`, or `feature` |
| labels | `pr-review-finding`, `aspect:<name>`, `severity:<level>`, `turn:<N>` |
| parent | PR review epic bead ID |
| external-ref | PR URL or specific PR comment URL |
| description | Full finding details, file location, suggested fix |

**Work beads** (output, created by this skill for non-trivial fixes):

| Field | Value |
|-------|-------|
| type | `task` |
| parent | PR review epic bead ID |
| deps | `discovered-from:<finding-id>` |
| description | What was fixed and how |

**Deferred work beads** (output, for findings the user defers):

| Field | Value |
|-------|-------|
| type | `task` |
| parent | Project epic (if clear) or none |
| labels | `deferred`, `aspect:<aspect>`, `from-pr:<number>` |
| external-ref | PR URL |
| deps | `discovered-from:<finding-id>` |
| description | Full context, file location, reason for deferral |

## Workflow

### Phase 1: Load

1. **Identify the PR.** Use `$ARGUMENTS` if provided, otherwise ask.
2. **Verify `bd`**: run `bd --version`. If it fails, stop and tell the
   user: "beads CLI (`bd`) is required but not found. Install beads and
   run `bd init` in the target project."
3. **Query the review epic bead:**

   ```bash
   bd list --labels "pr-review,pr:<number>" --status open --json
   ```

   If no review epic exists, stop: "No review findings for PR #N.
   Run `/review-pr <number>` first."

4. **Load all open findings:**

   ```bash
   bd list --parent <review-epic-id> --status open --json
   ```

   If no open findings, report "All findings already addressed" and stop.

5. **Locate worktree.** Run `git worktree list` and check whether one
   exists for the PR's branch. If so, `cd` into it and verify with
   `git branch --show-current`. If not, ask the user whether to create
   one. **MUST** use an existing worktree if one matches.

### Phase 2: Analyze Dependencies

The orchestrator reviews all open findings and identifies dependency
relationships using file overlap, conceptual overlap, and severity:

**File overlap** -- Two findings touching the same file should not be fixed
concurrently. Set a dependency so the higher-priority or earlier-in-file
finding is addressed first.

**Conceptual overlap** -- A design finding and a bug finding about the same
component. The design finding should be resolved first (it may change the
fix approach).

**Severity ordering** -- Critical findings block lower-severity findings in
the same file or area.

The orchestrator encodes all of these using `bd dep add`:

```bash
bd dep add <lower-priority-finding> --depends-on <higher-priority-finding>
```

The fix loop's "query ready findings" then naturally respects the graph.

### Phase 3: Triage

For each **open** finding bead, the orchestrator reads its description
and evaluates three dimensions to determine handling:

1. **Complexity** -- Is the fix straightforward or does it require judgment?
2. **Scope of change** -- Mechanical tweak or design/spec/contract shift?
3. **Deviation** -- Follows existing patterns or introduces new ones?

**Auto-fixable** (no user input needed):

- Clear bug with an obvious correct fix
- Mechanical changes (formatting, naming, lint)
- Low deviation from existing code and patterns

**Needs human judgment** -- present to user via `AskUserQuestion`:

- Fix requires a design or architectural choice
- Fix changes a spec, plan, or public contract
- Multiple valid approaches with meaningful trade-offs
- High deviation from existing patterns

Note: The `aspect` label (which review agent found the issue) does NOT
determine auto-fix vs needs-human. A security finding may be a simple
one-liner; a code quality finding may require an architectural decision.
The `aspect` label is used for model selection, not triage routing.

For each needs-human finding, use `AskUserQuestion` with:

- Concrete fix approach options (when the agent can propose them)
- A recommendation marked "(Recommended)" when there's a clear winner
- A "Defer" option
- AskUserQuestion provides "Other" automatically

**Complexity/model assignment:**

| Complexity | Criteria | Model |
|------------|---------------------------------------------|--------|
| low | Single file, mechanical change, obvious fix | haiku |
| medium | Few files, some judgment, clear approach | sonnet |
| high | Cross-cutting, architectural, needs context | opus |

**Deferral handling:**

When the user chooses "Defer":

1. Add `deferred` label to the finding:

   ```bash
   bd update <finding-id> --add-label deferred
   ```

2. Create a deferred work bead in the appropriate project epic (or
   top-level if no clear epic):

   ```bash
   bd create "<description of the work>" \
     --type task \
     --parent <project-epic-id-or-omit> \
     --labels "deferred,aspect:<aspect>,from-pr:<number>" \
     --external-ref "https://github.com/{owner}/{repo}/pull/<number>" \
     --description "<full context, file location, reason for deferral>" \
     --silent
   ```

3. Link back to the finding:

   ```bash
   bd dep add <deferred-work-bead> --depends-on <finding-id> --type discovered-from
   ```

### Phase 4: Fix Loop

Loop while open, non-deferred findings remain:

1. **Query ready findings** (no unresolved deps among open beads):

   ```bash
   bd list --parent <epic-id> --status open --json
   ```

   Filter to findings whose dependencies are all closed.

2. **Pick up to 3** ready findings.

3. **For each non-trivial finding**, create a work bead first:

   ```bash
   bd create "Fix(<finding-id>): <short desc>" \
     --type task \
     --parent <review-epic-id> \
     --description "<work to be done>" \
     --deps "blocks:<finding-id>" \
     --silent
   ```

   The work bead blocks the finding bead -- the finding cannot be
   closed until the fix work is complete.

4. **Launch fix sub-agents** (up to 3 concurrent). Each receives:

   - Finding bead ID and description
   - Work bead ID (if created)
   - File location and suggested fix from the finding
   - Model assignment from triage

   Sub-agent implements the fix and reports what it did.
   Sub-agent does NOT close or update any beads.

5. **Wait** for all sub-agents in this round to complete.

6. **Launch a review agent** (sonnet) for this round's fixes. Receives:

   - `git diff` of changes made
   - Finding descriptions for each fix
   - What each sub-agent reported

   Returns per-finding: `PASS` | `FAIL: <reason>`

7. **For PASS findings:**

   - Orchestrator closes the work bead (if any):
     `bd update <work-id> --status closed`
   - Orchestrator closes the finding bead:
     `bd update <finding-id> --status closed`

8. **For FAIL findings:**

   - Add comment: `bd comments add <finding-id> "Review failed: <reason>"`
   - Re-queue (stays open, eligible for next round)
   - Max 2 retries per finding. After 2 failures, escalate to user.

### Phase 5: Verify

Launch a **sonnet sub-agent** to run quality gates:

1. Detect project type (`Taskfile.yml`, `pyproject.toml`, `Cargo.toml`,
   `package.json`, `build.gradle`, etc.)
2. Run appropriate commands for unit tests, integration tests, build,
   and lint
3. If failures: sub-agent reviews error, fixes, re-runs
4. **Max 3 attempts.** If gates still fail after 3 rounds, report the
   remaining failures to the user for guidance.
5. Do NOT proceed to Phase 6 until all gates pass.

### Phase 6: Ship

1. **Commit** using the `commit-commands:commit` skill.
2. **Push** to the PR branch.
3. **Post summary comment** on the PR:

   Write to a temp file and post:

   ```bash
   gh pr comment <number> --body-file /tmp/review-response.md
   ```

   Template:

   ```markdown
   <!-- address-review:<epic-id>:response -->
   ## Review Response

   `bd list --parent <epic-id>`

   Fixed N | Deferred N | Failed N

   | Finding | Status | Work |
   |---------|--------|------|
   | <finding-id> | Fixed | <work-bead-id> |
   | <finding-id> | Deferred | <deferred-bead-id> |
   | <finding-id> | Failed (escalated) | -- |
   ```

## Hard Constraints

| Constraint | Reason |
|------------------------------|---------------------------|
| **MUST NOT** close the review epic | PR merge triggers closure |
| **MUST NOT** merge the PR | Reviewer's decision |
| **MUST** use worktree | Avoid branch conflicts |
| **MUST** use `AskUserQuestion` for human judgment | Structured input with options |
| **MUST** filter `--status open` in all bead queries | Skip already-handled findings |
| **MUST NOT** let sub-agents close beads | Orchestrator owns bead lifecycle |
| **MUST** use long flags for all `bd` commands | Clarity for sub-agents |

## Skill Metadata

```yaml
name: address-review-findings
description: >-
  Processes findings from review-pr by working through beads in the review
  epic. Use when the user asks to "address review findings", "fix review
  issues", "work through review beads", or "process review-pr findings".
argument-hint: "[pr-number]"
```

## Relationship to respond-to-pr-comments

| | respond-to-pr-comments | address-review-findings |
|---|---|---|
| Input source | GitHub PR comments | Beads from review epic |
| Scope | Any PR with comments | PRs that have been review-pr'd |
| GitHub comment parsing | Yes (pr_comments script) | No |
| Cross-referencing | Matches comments to beads | N/A -- beads are the source |
| Dependency analysis | None | Phase 2 (file/concept overlap) |
| User interaction | Asks about all unclear comments | Asks about design/feature only |

Future: `respond-to-pr-comments` may delegate to `address-review-findings`
when a review epic exists for the PR.

## bd CLI Reference

Subset of commands used by this skill. All commands use long flags only.

### bd list -- Query findings

```bash
bd list --parent <epic-id> --status open --json
bd list --parent <epic-id> --status open --label "aspect:code" --json
bd list --labels "pr-review,pr:<number>" --json
```

### bd create -- Create work and deferred beads

```bash
bd create "<title>" \
  --type task \
  --parent <epic-id> \
  --labels "label1,label2" \
  --external-ref "<url>" \
  --deps "discovered-from:<finding-id>" \
  --description "<details>" \
  --silent
```

### bd update -- Close beads, add labels

```bash
bd update <id> --status closed
bd update <id> --add-label deferred
bd update <id> --status in_progress
```

### bd dep add -- Set dependencies

```bash
bd dep add <issue-id> --depends-on <dependency-id>                          # blocks (default type)
bd dep add <issue-id> --depends-on <dependency-id> --type discovered-from   # traceability
bd dep add <issue-id> --depends-on <dependency-id> --type validates         # review validates fix
bd dep add <issue-id> --depends-on <dependency-id> --type caused-by         # root cause link
```

### bd dep relate -- Bidirectional link (no blocking)

```bash
bd dep relate <id1> <id2>
```

### bd dep list -- Check dependencies

```bash
bd dep list <id>
```

### bd comments add -- Annotate beads

```bash
bd comments add <id> "Review failed: <reason>"
bd comments add <id> --file notes.txt
```

### bd search -- Find project epics

```bash
bd search "<query>" --status open --type epic --json
```

## Addendum: Design Doc Bug Fix

The 2026-02-15 beads integration design doc specifies `--type task` for
the PR review parent bead (line 70, line 117). The implementation in
`review-pr/SKILL.md` correctly uses `--type epic`. The design doc should
be updated to match.
