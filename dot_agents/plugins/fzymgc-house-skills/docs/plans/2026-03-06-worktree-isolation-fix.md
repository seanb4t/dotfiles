# Worktree Isolation Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix worktree-isolated agents so they commit changes in their
worktree branch and never modify the base repo, with worktrees placed
in a sibling directory.

**Architecture:** WorktreeCreate/WorktreeRemove hooks in settings.json
delegate to shell scripts that place worktrees in `<repo>_worktrees/`.
All 11 worktree-isolated agents get an Environment block for worktree
awareness. fix-worker and verification-runner get a Commit protocol.
The address-findings orchestrator passes a fix manifest to
verification-runner and selects model by complexity.

**Tech Stack:** Bash (hooks), Markdown (agent/skill prompts), JSON (settings)

---

## Task 1: Worktree Hook Scripts

**Files:**

- Create: `.claude/hooks/worktree-create.sh`
- Create: `.claude/hooks/worktree-remove.sh`
- Modify: `.claude/settings.json`

### Step 1: Create worktree-create.sh

```bash
#!/usr/bin/env bash
# WorktreeCreate hook: create worktrees in sibling directory
# Input: JSON on stdin with "name" field
# Output: print the worktree path to stdout (framework reads this)
set -euo pipefail

INPUT=$(cat)
NAME=$(echo "$INPUT" | jq -r '.name // empty')

if [[ -z "$NAME" ]]; then
  echo "ERROR: no worktree name provided" >&2
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")
WORKTREE_PARENT="$(dirname "$REPO_ROOT")/${REPO_NAME}_worktrees"
WORKTREE_PATH="${WORKTREE_PARENT}/${NAME}"

mkdir -p "$WORKTREE_PARENT"
git worktree add "$WORKTREE_PATH" -b "worktree/${NAME}" HEAD

# Install git hooks in the new worktree
if [[ -f "${REPO_ROOT}/lefthook.yml" ]]; then
  (cd "$WORKTREE_PATH" && lefthook install 2>/dev/null) || true
fi

echo "$WORKTREE_PATH"
```

#### Step 2: Create worktree-remove.sh

```bash
#!/usr/bin/env bash
# WorktreeRemove hook: remove worktrees from sibling directory
# Input: JSON on stdin with "path" field
set -euo pipefail

INPUT=$(cat)
WORKTREE_PATH=$(echo "$INPUT" | jq -r '.path // empty')

if [[ -z "$WORKTREE_PATH" || ! -d "$WORKTREE_PATH" ]]; then
  exit 0
fi

git worktree remove --force "$WORKTREE_PATH" 2>/dev/null || true

# Clean up empty parent directory
PARENT=$(dirname "$WORKTREE_PATH")
if [[ -d "$PARENT" ]] && [[ -z "$(ls -A "$PARENT")" ]]; then
  rmdir "$PARENT" 2>/dev/null || true
fi
```

#### Step 3: Make scripts executable

Run: `chmod +x .claude/hooks/worktree-create.sh .claude/hooks/worktree-remove.sh`

#### Step 4: Update settings.json

Modify `.claude/settings.json` to add WorktreeCreate and WorktreeRemove hooks
alongside the existing PostToolUse hook:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/post-edit-format.sh",
            "timeout": 15
          }
        ]
      }
    ],
    "WorktreeCreate": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/worktree-create.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "WorktreeRemove": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/worktree-remove.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

#### Step 5: Verify hook scripts parse correctly

Run: `echo '{"name":"test-wt"}' | bash .claude/hooks/worktree-create.sh`
Expected: creates worktree at `../<repo>_worktrees/test-wt`, prints path

Run: `echo "{\"path\":\"$(dirname $(git rev-parse --show-toplevel))/fzymgc-house-skills_worktrees/test-wt\"}" | bash .claude/hooks/worktree-remove.sh`
Expected: removes the test worktree

#### Step 6: Commit

```bash
git add .claude/hooks/worktree-create.sh .claude/hooks/worktree-remove.sh .claude/settings.json
git commit -m "feat(pr-review): add worktree hooks for sibling directory layout

WorktreeCreate/WorktreeRemove hooks place agent worktrees in
<repo>_worktrees/ sibling directory instead of nested .claude/worktrees/.
This prevents LSP server confusion from nested project roots."
```

---

## Task 2: Fix fix-worker Agent

**Files:**

- Modify: `pr-review/agents/fix-worker.md` (entire file rewrite)

### Step 1: Rewrite fix-worker.md

The new version adds three sections: Environment (worktree awareness),
updated Process (with commit step), and expanded Constraints.

````markdown
---
name: fix-worker
description: >-
  Implements code fixes for PR review findings. Used by the
  address-findings orchestrator. Receives a finding bead ID, reads
  the finding details, and applies the fix in its isolated worktree.
model: sonnet
isolation: worktree
tools: Read, Edit, Write, Grep, Glob, Bash
---

# Fix Worker

You are a focused code fix agent. You receive a single review finding
and implement the minimal correct fix.

## Environment

You are running in an isolated git worktree. On startup:

1. Run `pwd` and `git branch --show-current` to confirm your location
2. Verify you are NOT on `main` — you should be on a `worktree/*` branch
3. If anything looks wrong, STOP and report STATUS: FAILED

**Path rules:**

- Use ONLY relative paths for all file operations
- Do NOT `cd` outside your working directory
- Do NOT use absolute paths from finding descriptions — translate them
  to relative paths within your worktree

## Input Variables

The orchestrator provides these in the task prompt:

- `FINDING_BEAD_ID` — the bead describing the issue to fix
- `WORK_BEAD_ID` — your work tracking bead
- `FILE_LOCATION` — file and line(s) where the issue is (relative path)
- `SUGGESTED_FIX` — the reviewer's suggestion for how to fix it

## Process

1. **Verify environment** (see Environment section above)
2. **Read the finding:** `bd show $FINDING_BEAD_ID`
3. **Read the affected file(s)** around the reported location
4. **Understand** the issue and the suggested fix
5. **Implement** the minimal correct fix
6. **Verify** the fix addresses the finding (re-read the changed code)
7. **Commit** your changes:

   ```bash
   git add <file1> <file2> ...
   git commit -m "fix(<finding-bead-id>): <one-line description>"
   ```

8. **Confirm** the commit landed: `git log --oneline -1`

## Fix-Worker Output

Return a structured result to the orchestrator:

```text
STATUS: FIXED | PARTIAL | FAILED
FINDING: <bead-id>
FILES_CHANGED: <file1>, <file2>, ...
DESCRIPTION: <one-line summary of what was changed>
WORKTREE_BRANCH: <branch name from git branch --show-current>
```

## Fix-Worker Constraints

- Fix ONLY the specific finding — no drive-by improvements
- Match existing code style and patterns in the project
- Do NOT close or update beads — the orchestrator manages bead lifecycle
- Do NOT run tests — the verification-runner agent handles that
- Do NOT modify files outside the scope of the finding
- MUST commit changes before returning — uncommitted changes are lost
- MUST use relative paths only — absolute paths may target the wrong repo
- If the fix requires a design decision, report STATUS: PARTIAL with
  a description of what decision is needed
````

#### Step 2: Verify markdown formatting

Run: `rumdl check pr-review/agents/fix-worker.md`
Expected: no errors (or only auto-fixable ones)

#### Step 3: Commit

```bash
git add pr-review/agents/fix-worker.md
git commit -m "fix(fix-worker): add worktree awareness and commit protocol

fix-worker now verifies its worktree environment on startup, uses only
relative paths, and commits changes before returning. This fixes both
the 'changes lost' and 'edits in base repo' failure modes."
```

---

## Task 3: Enhance verification-runner Agent

**Files:**

- Modify: `pr-review/agents/verification-runner.md` (entire file rewrite)

### Step 1: Rewrite verification-runner.md

New version adds: Environment block, fix manifest input, alignment
checking, conditional commit for lint fixes.

````markdown
---
name: verification-runner
description: >-
  Validates fixes and runs project quality gates after fixes are applied.
  Used by the address-findings orchestrator. Receives a fix manifest with
  problem/fix/change context and verifies alignment plus lint/build/tests.
model: sonnet
isolation: worktree
tools: Read, Grep, Glob, Bash
---

# Verification Runner

You are a verification agent. You validate that fixes address their
findings and that the project's quality gates pass.

## Environment

You are running in an isolated git worktree. On startup:

1. Run `pwd` and `git branch --show-current` to confirm your location
2. Verify you are NOT on `main` — you should be on a `worktree/*` branch
3. If anything looks wrong, STOP and report STATUS: FAIL

**Path rules:**

- Use ONLY relative paths for all file operations
- Do NOT `cd` outside your working directory

## Input

The orchestrator provides a **fix manifest** in the task prompt:

```text
## Fix Manifest

| Finding | Problem | Proposed Fix | Actual Changes |
|---------|---------|--------------|----------------|
| <bead-id> | <problem statement> | <suggested fix> | <files + description> |
```
````

## Process

### 1. Fix Alignment

For each finding in the manifest:

1. Read the problem statement and proposed fix
2. Read the actual changed files (use relative paths from "Actual Changes")
3. Assess whether the change addresses the root cause (not just symptoms)
4. Check the change does not introduce new issues
5. Verify the change is minimal and focused

### 2. Quality Gates

Detect project type by checking for:

- `Taskfile.yml` → `task test`, `task lint`, `task build`
- `pyproject.toml` → `pytest`, `ruff check`, `ruff format --check`
- `Cargo.toml` → `cargo test`, `cargo clippy`, `cargo build`
- `package.json` → `npm test`, `npm run lint`, `npm run build`
- `Makefile` → `make test`, `make lint`, `make build`
- `go.mod` → `go test ./...`, `go vet ./...`, `go build ./...`

Run each applicable gate in order: lint → build → test

### 3. Fix-up (if needed)

If a lint gate fails with auto-fixable issues:

1. Apply the fix (e.g., `ruff check --fix`)
2. Re-run the gate to confirm it passes
3. Commit the fix-up:

   ```bash
   git add <fixed-files>
   git commit -m "fix(lint): <description of lint fixes>"
   ```

4. Max 3 attempts per gate

### 4. Report

Return the structured result.

## Verification-Runner Output

```text
STATUS: PASS | FAIL

## Fix Alignment
<finding-id>: ALIGNED | MISALIGNED: <reason>
...

## Quality Gates
lint: PASS | FAIL
build: PASS | FAIL
tests: PASS | FAIL

FAILURES: <details or "none">
```

## Verification-Runner Constraints

- Run gates in order: lint, build, tests
- Do NOT fix test failures by deleting or weakening tests
- Do NOT fix alignment issues — only report them
- Only commit if you made lint fix-up changes
- Report honestly — if gates fail after 3 attempts, say so
- Include enough failure detail for the orchestrator to act on

### Step 2: Verify formatting

Run: `rumdl check pr-review/agents/verification-runner.md`

#### Step 3: Commit

```bash
git add pr-review/agents/verification-runner.md
git commit -m "feat(verification-runner): add fix alignment checking and worktree awareness

verification-runner now receives a fix manifest with problem/fix/change
context, validates fixes address their findings, and includes worktree
environment verification. Lint fix-ups are committed before returning."
```

---

## Task 4: Add Environment Block to Review Agents

**Files (9 agents):**

- Modify: `pr-review/agents/code-reviewer.md`
- Modify: `pr-review/agents/silent-failure-hunter.md`
- Modify: `pr-review/agents/api-contract-checker.md`
- Modify: `pr-review/agents/code-simplifier.md`
- Modify: `pr-review/agents/security-auditor.md`
- Modify: `pr-review/agents/spec-compliance.md`
- Modify: `pr-review/agents/comment-analyzer.md`
- Modify: `pr-review/agents/pr-test-analyzer.md`
- Modify: `pr-review/agents/type-design-analyzer.md`

### Step 1: Add Environment block to each agent

Insert the following block immediately after the first `#` heading and
introductory paragraph in each agent file. Place it BEFORE any existing
`## Core Responsibilities`, `## Input`, or `## Process` section:

```markdown
## Environment

You are running in an isolated git worktree. On startup:

1. Run `pwd` and `git branch --show-current` to confirm your location
2. Verify you are NOT on `main` — you should be on a `worktree/*` branch
3. If anything looks wrong, STOP and report the error to the orchestrator

**Path rules:**

- Use ONLY relative paths for all file operations
- Do NOT `cd` outside your working directory
- Do NOT use absolute paths from diffs or PR metadata — translate them
  to relative paths within your worktree
```

Apply this to all 9 review agents listed above. Each agent keeps its
existing content unchanged — only the Environment block is inserted.

#### Step 2: Verify all agents pass linting

Run: `for f in pr-review/agents/*.md; do echo "=== $f ==="; rumdl check "$f"; done`
Expected: all pass (or only auto-fixable warnings)

#### Step 3: Commit

```bash
git add pr-review/agents/code-reviewer.md \
       pr-review/agents/silent-failure-hunter.md \
       pr-review/agents/api-contract-checker.md \
       pr-review/agents/code-simplifier.md \
       pr-review/agents/security-auditor.md \
       pr-review/agents/spec-compliance.md \
       pr-review/agents/comment-analyzer.md \
       pr-review/agents/pr-test-analyzer.md \
       pr-review/agents/type-design-analyzer.md
git commit -m "fix(agents): add worktree environment awareness to all review agents

All 9 review agents now verify their worktree location on startup and
use only relative paths. Prevents accidental edits to the base repo."
```

---

## Task 5: Update address-findings Orchestrator

**Files:**

- Modify: `pr-review/skills/address-findings/SKILL.md`

Changes are in three areas:

### Step 1: Update Phase 4 fix-worker dispatch (lines 207-219)

Replace the dispatch template to include the standardized commit format
expectation:

````text
4. **Launch fix-worker agents** via Task (up to 3 concurrent):

   ```text
   subagent_type: "fix-worker"
   isolation: worktree
   model: sonnet  (or opus for complex/vague findings)
   prompt: |
     FINDING_BEAD_ID: <finding-id>
     WORK_BEAD_ID: <work-bead-id>
     FILE_LOCATION: <relative-path:line>
     SUGGESTED_FIX: <from finding description>
     Implement the fix. Commit with message:
       fix(<finding-id>): <one-line description>
     Report STATUS, FILES_CHANGED, DESCRIPTION, WORKTREE_BRANCH.
     Do NOT close or update any beads.
   ```
````

Note: FILE_LOCATION must use a **relative path**. Strip any absolute
prefix before dispatching.

#### Step 2: Update Phase 4b worktree paths (lines 225-253)

Replace the merge and cleanup section to reference sibling worktree
paths:

````markdown
### Phase 4b: Merge Fix Branches

For each FIXED result, in dependency order:

1. Merge into the PR branch:

   ```bash
   git merge --no-ff <worktree-branch> -m "fix(<finding-id>): <description>"
   ```

2. If merge conflict: mark FAILED, add bead comment, re-queue for
   next round.
3. Clean up worktree (sibling directory):

   ```bash
   git worktree remove ../<repo>_worktrees/<worktree-name>
   ```

Same-file findings serialized in Phase 2 prevent most conflicts.

4. **Commit after each merge round.** After all branches in a batch
   are merged, create a checkpoint commit before the next loop
   iteration:

   ```bash
   git add -A && git commit -m "fix: address review findings (batch N)"
   ```

   This prevents worktree-isolated agents in the next round from
   corrupting the working tree via stale branch references. Never
   dispatch new fix-worker agents with uncommitted changes in the
   main working tree.
````

#### Step 3: Update Phase 5 verification dispatch (lines 275-292)

Replace the verification-runner dispatch to pass a fix manifest and
select model by complexity:

````markdown
## Phase 5: Verify

Build a **fix manifest** from the collected fix-worker results:

```text
## Fix Manifest

| Finding | Problem | Proposed Fix | Actual Changes |
|---------|---------|--------------|----------------|
| <bead-id> | <from finding description> | <suggested fix> | <files + description from fix-worker> |
```

Select the verification model based on batch complexity:

| Batch composition | Model |
|---|---|
| All mechanical / single-file fixes | sonnet |
| Any cross-cutting / architectural / vague fix in batch | opus |

Dispatch a verification-runner agent:

```text
subagent_type: "verification-runner"
isolation: worktree
model: <sonnet or opus per table above>
prompt: |
  <fix manifest table>

  Validate fix alignment and run quality gates.
  Report per-finding alignment AND gate status.
```

- **Any MISALIGNED finding**: treat as review-gate FAIL, re-queue
- **Gate FAIL**: report failure details to user. Do NOT proceed to Phase 6.
- **All ALIGNED + gates PASS**: proceed.
````

#### Step 4: Verify formatting and line count

Run: `rumdl check pr-review/skills/address-findings/SKILL.md`
Run: `wc -l pr-review/skills/address-findings/SKILL.md`
Expected: under 500 lines

#### Step 5: Commit

```bash
git add pr-review/skills/address-findings/SKILL.md
git commit -m "feat(address-findings): fix manifest verification and sibling worktree paths

- Phase 4: standardize commit format in fix-worker dispatch
- Phase 4b: update worktree cleanup to sibling directory layout
- Phase 5: pass fix manifest to verification-runner with problem/fix/change
  context; select model (sonnet/opus) based on batch complexity"
```

---

## Task 6: Update respond-to-comments Worktree References

**Files:**

- Modify: `pr-review/skills/respond-to-comments/SKILL.md:121-124`

### Step 1: Update worktree location instructions

Replace lines 121-124:

```markdown
6. **Locate the worktree.** Run `git worktree list` and check whether one
   exists for the PR's branch. Worktrees are in the sibling
   `<repo>_worktrees/` directory. If one matches, `cd` into it and
   verify with `git branch --show-current`. If not, ask the user
   whether to create one.
   **MUST** use an existing worktree if one matches.
```

#### Step 2: Verify formatting

Run: `rumdl check pr-review/skills/respond-to-comments/SKILL.md`

#### Step 3: Commit

```bash
git add pr-review/skills/respond-to-comments/SKILL.md
git commit -m "fix(respond-to-comments): update worktree location to sibling directory"
```

---

## Task 7: Document Sibling Worktree Convention in CLAUDE.md

**Files:**

- Modify: `CLAUDE.md:141` (add new Gotchas subsection)

### Step 1: Add worktree convention after the "Auto-Formatting" gotcha

Insert after line 151 (end of Auto-Formatting section):

````markdown
### Worktree Layout

Agent worktrees are created in a **sibling directory** to avoid nesting
repos (which confuses LSP servers):

```text
<repo>/                    # main repo
<repo>_worktrees/          # worktree parent (sibling)
  fix-worker-abc/          # one worktree per agent invocation
  verification-runner-def/
```
````

WorktreeCreate/WorktreeRemove hooks in `.claude/settings.json` handle
this automatically. Do NOT manually create worktrees inside
`.claude/worktrees/`.

#### Step 2: Verify formatting

Run: `rumdl check CLAUDE.md`

#### Step 3: Commit

```bash
git add CLAUDE.md
git commit -m "docs: document sibling worktree layout convention"
```
