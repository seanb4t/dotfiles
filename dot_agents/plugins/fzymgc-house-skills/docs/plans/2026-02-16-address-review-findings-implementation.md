# Address Review Findings — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a new `address-review-findings` skill that processes
review-pr finding beads through a dependency-aware fix loop with batch
review gates.

**Architecture:** Single SKILL.md orchestrator skill with a
`references/bd-reference.md` companion file. No scripts needed — the
skill works entirely through `bd` CLI, `git`, `gh`, and the Task tool
for sub-agents. Follows the same directory structure as existing skills.

**Tech Stack:** SKILL.md (YAML frontmatter + markdown), `bd` CLI for
bead operations, `gh` CLI for PR interaction, Task tool for sub-agent
dispatch.

**Design doc:** `docs/plans/2026-02-16-address-review-findings-design.md`

---

## Task 1: Create skill directory and bd reference file

**Files:**

- Create: `fzymgc-house/skills/address-review-findings/references/bd-reference.md`

### Step 1: Create the bd CLI reference file

Copy the bd CLI reference from the design doc's "bd CLI Reference" section
(lines 339-404) into `references/bd-reference.md`. Add a header explaining
this is for sub-agent context:

```markdown
# bd CLI Reference

Subset of `bd` commands used by the address-review-findings skill.
All commands use long flags only — no shorthand.

## bd list — Query findings

...
```

Include all sections from the design doc: `bd list`, `bd create`,
`bd update`, `bd dep add`, `bd dep relate`, `bd dep list`,
`bd comments add`, `bd search`.

#### Step 2: Verify the file

Run: `cat fzymgc-house/skills/address-review-findings/references/bd-reference.md | head -5`
Expected: The header and first section appear.

#### Step 3: Commit

```text
feat(skills): add bd CLI reference for address-review-findings
```

---

### Task 2: Create SKILL.md frontmatter and Phase 1 (Load)

**Files:**

- Create: `fzymgc-house/skills/address-review-findings/SKILL.md`

#### Step 1: Write the frontmatter

Use the metadata from the design doc (lines 316-323), plus allowed-tools
modeled on respond-to-pr-comments. The skill needs:

- `Bash(bd *)` commands: `create`, `list`, `update`, `show`, `dep`,
  `query`, `comments`, `search`
- `Bash(git *)` and `Bash(gh *)` for worktree and PR operations
- `Task` for sub-agent dispatch
- `Read`, `Edit`, `Write`, `Grep`, `Glob` for code operations

```yaml
---
name: address-review-findings
description: >-
  Processes findings from review-pr by working through beads in the review
  epic. Use when the user asks to "address review findings", "fix review
  issues", "work through review beads", or "process review-pr findings".
argument-hint: "[pr-number]"
allowed-tools:
  - Task
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - "Bash(git *)"
  - "Bash(gh *)"
  - "Bash(bd create *)"
  - "Bash(bd list *)"
  - "Bash(bd update *)"
  - "Bash(bd show *)"
  - "Bash(bd dep *)"
  - "Bash(bd query *)"
  - "Bash(bd comments *)"
  - "Bash(bd search *)"
metadata:
  author: fzymgc-house
  version: 0.1.0
---
```

#### Step 2: Write Phase 1 (Load)

Below the frontmatter, write the skill body starting with a title and
Phase 1. Transcribe from the design doc (lines 76-102), keeping the
same structure: identify PR, verify bd, query review epic, load open
findings, locate worktree.

Reference the bd-reference file:

```markdown
# Address Review Findings

Process findings from a `review-pr` run by working through the beads
in the review epic. Each finding is triaged, fixed by a sub-agent,
batch-reviewed, and closed.

**Read** `references/bd-reference.md` for the full `bd` CLI subset
used by this skill.

## Phase 1: Load

...
```

#### Step 3: Verify line count

Run: `wc -l fzymgc-house/skills/address-review-findings/SKILL.md`
Expected: Under 100 lines at this point.

#### Step 4: Commit

```text
feat(skills): add address-review-findings skill with Phase 1
```

---

### Task 3: Write Phase 2 (Analyze Dependencies)

**Files:**

- Modify: `fzymgc-house/skills/address-review-findings/SKILL.md`

#### Step 1: Append Phase 2

Transcribe from design doc (lines 104-126). Cover:

- File overlap detection (two findings on same file)
- Conceptual overlap (design finding + bug on same component)
- Severity ordering (critical blocks lower-severity in same area)
- Using `bd dep add <id> --depends-on <id>` to encode relationships
- Explain that the fix loop naturally respects the dependency graph

#### Step 2: Verify

Run: `wc -l fzymgc-house/skills/address-review-findings/SKILL.md`
Expected: Under 150 lines.

#### Step 3: Commit

```text
feat(skills): add Phase 2 dependency analysis to address-review-findings
```

---

### Task 4: Write Phase 3 (Triage)

**Files:**

- Modify: `fzymgc-house/skills/address-review-findings/SKILL.md`

#### Step 1: Append Phase 3

Transcribe from design doc (lines 128-197). This is the longest phase.
Cover:

- Three evaluation dimensions (complexity, scope of change, deviation)
- Auto-fixable criteria
- Needs-human criteria
- Explicit note that `aspect` label does NOT drive triage routing
- `AskUserQuestion` usage with concrete fix options and recommendations
- Complexity/model assignment table
- Deferral handling: add `deferred` label, create deferred work bead
  with `from-pr:<number>` label, `external-ref`, `discovered-from` dep

#### Step 2: Verify line count stays manageable

Run: `wc -l fzymgc-house/skills/address-review-findings/SKILL.md`
Expected: Under 250 lines.

#### Step 3: Commit

```text
feat(skills): add Phase 3 triage to address-review-findings
```

---

### Task 5: Write Phase 4 (Fix Loop)

**Files:**

- Modify: `fzymgc-house/skills/address-review-findings/SKILL.md`

#### Step 1: Append Phase 4

Transcribe from design doc (lines 199-258). Cover the 8-step loop:

1. Query ready findings (open, deps all closed)
2. Pick up to 3
3. Create work beads for non-trivial findings (with `blocks` dep,
   proper title format `Fix(<finding-id>): <desc>`, description)
4. Launch fix sub-agents (up to 3 concurrent via Task tool)
   — sub-agents do NOT close beads
5. Wait for round to complete
6. Launch review agent (sonnet) for batch review — PASS/FAIL per finding
7. PASS: orchestrator closes work bead then finding bead
8. FAIL: add comment, re-queue, max 2 retries then escalate

#### Step 2: Verify

Run: `wc -l fzymgc-house/skills/address-review-findings/SKILL.md`
Expected: Under 350 lines.

#### Step 3: Commit

```text
feat(skills): add Phase 4 fix loop to address-review-findings
```

---

### Task 6: Write Phase 5 (Verify) and Phase 6 (Ship)

**Files:**

- Modify: `fzymgc-house/skills/address-review-findings/SKILL.md`

#### Step 1: Append Phase 5 (Verify)

Transcribe from design doc (lines 260-271). Cover:

- Sonnet sub-agent for quality gates
- Project type detection
- Test/lint/build execution
- Max 3 attempts, escalate on failure
- Gate before Phase 6

#### Step 2: Append Phase 6 (Ship)

Transcribe from design doc (lines 273-300). Cover:

- Commit using `commit-commands:commit` skill
- Push to PR branch
- Post summary comment via `gh pr comment` with template
- HTML comment marker for machine detection

#### Step 3: Append Hard Constraints table

Transcribe from design doc (lines 302-312).

#### Step 4: Verify total line count

Run: `wc -l fzymgc-house/skills/address-review-findings/SKILL.md`
Expected: Under 500 lines (skill best practice limit).

#### Step 5: Commit

```text
feat(skills): add Phase 5-6 and constraints to address-review-findings
```

---

### Task 7: Fix the design doc bug in beads integration doc

**Files:**

- Modify: `docs/plans/2026-02-15-beads-review-integration-design.md`

#### Step 1: Fix type field in PR Review Bead table

At line 70, change `type` from `task` to `epic`:

```markdown
| type | `epic` |
```

#### Step 2: Fix `--type task` in create command

At line 117, change `--type task` to `--type epic`:

```bash
  --type epic \
```

#### Step 3: Verify both changes

Run: `grep -n "type.*task\|type.*epic" docs/plans/2026-02-15-beads-review-integration-design.md`
Expected: Lines 70 and 117 now say `epic`, other lines with `task` are
for finding beads (correct).

#### Step 4: Commit

```text
fix(docs): correct PR review bead type from task to epic in design doc
```

---

### Task 8: Update CLAUDE.md with new skill

**Files:**

- Modify: `CLAUDE.md`

#### Step 1: Add address-review-findings to Available Skills section

Add a bullet after the `respond-to-pr-comments` entry:

```markdown
- **address-review-findings** - Processes review-pr findings by working through
  beads in the review epic. Dependency-aware fix loop with batch review gates.
```

#### Step 2: Verify

Run: `grep "address-review" CLAUDE.md`
Expected: The new bullet appears.

#### Step 3: Commit

```text
docs: add address-review-findings to CLAUDE.md skill list
```

---

### Task 9: Validate skill structure

#### Step 1: Check skill loads

Run: `claude plugin install . --force` (or equivalent local install)
to verify the plugin loads without errors.

#### Step 2: Check SKILL.md line count

Run: `wc -l fzymgc-house/skills/address-review-findings/SKILL.md`
Expected: Under 500 lines.

#### Step 3: Verify frontmatter

Run: `head -35 fzymgc-house/skills/address-review-findings/SKILL.md`
Expected: Valid YAML frontmatter with name, description, argument-hint,
allowed-tools, metadata.

#### Step 4: Run linters

Run: `rumdl check fzymgc-house/skills/address-review-findings/SKILL.md`
Run: `rumdl check fzymgc-house/skills/address-review-findings/references/bd-reference.md`
Expected: No errors.

#### Step 5: Commit any lint fixes if needed

```text
fix(skills): lint fixes for address-review-findings
```
