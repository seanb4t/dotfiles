---
name: respond-to-comments
description: >-
  Manages GitHub PR review comments. Use when the user asks to "list PR comments",
  "check PR feedback", "respond to PR comments", "address reviewer feedback",
  "fix PR review issues", "work through PR review", or "acknowledge comments".
  Handles both quick lookups and full review-response workflows.
argument-hint: "[pr-number]"
allowed-tools:
  - "Bash(${CLAUDE_PLUGIN_ROOT}/skills/respond-to-comments/scripts/pr_comments *)"
  - "Bash(git *)"
  - "Bash(jj st)"
  - "Bash(jj st *)"
  - "Bash(jj log *)"
  - "Bash(jj diff *)"
  - "Bash(test *)"
  - "Bash(jj root)"
  - "Bash(jj workspace *)"
  - "Bash(jj bookmark *)"
  - "Bash(jj git *)"
  - "Bash(jj commit *)"
  - "Bash(gh *)"
  - "Bash(bd create *)"
  - "Bash(bd list *)"
  - "Bash(bd update *)"
  - "Bash(bd show *)"
  - "Bash(bd dep *)"
  - "Bash(bd query *)"
  - "Bash(bd comments *)"
  - "Bash(task *)"
  - Read
  - Edit
  - Write
  - Grep
  - Glob
metadata:
  author: fzymgc-house
  version: 1.0.0 # x-release-please-version
---

# PR Comment Operations

## Contents

- [VCS Detection](#vcs-detection)
- [Commands](#commands)
- [Quick lookup vs full workflow](#quick-lookup-vs-full-workflow)
- [Full Review-Response Workflow](#full-review-response-workflow)
- [Hard Constraints](#hard-constraints)
- [Notes](#notes)

## VCS Detection

Follow the procedure in `pr-review/references/vcs-detection-preamble.md` to
detect git vs jj and verify your location. Use `gh` CLI for GitHub
operations regardless of VCS.

**Execute** the bundled script using the full absolute path from
your allowed-tools Bash pattern. The script outputs ready-to-run
commands with its own absolute path — copy-paste those directly.

## Commands

```bash
scripts/pr_comments list <pr> [--unacked]       # List comments
scripts/pr_comments get <pr> <id> [--save <p>]  # Get comment
scripts/pr_comments latest <pr>                 # Most recent
scripts/pr_comments ack <pr> <id>               # Acknowledge
scripts/pr_comments comment <pr> --file <path>  # Post comment
scripts/pr_comments comment <pr> "text"         # Post inline
```

Comment IDs: `RC_*` = review comment (inline on code), `R_*` = review (approve/request/comment).

## Quick lookup vs full workflow

**Quick lookup** (e.g., "list PR comments", "check what reviewers said"):
Run the relevant command above and present the output. Done.

**Full workflow** (e.g., "address PR feedback", "fix PR review issues"):
Follow the workflow below.

---

## Full Review-Response Workflow

Copy this checklist and update as you go:

```text
- [ ] Phase 1: Read unacked comments, query beads for prior findings, cross-reference, locate worktree
- [ ] Phase 2: Categorize comments, confirm with user
- [ ] Phase 3: Implement fixes, update beads (close findings, create work beads)
- [ ] Phase 4: All quality gates pass (test, build, lint)
- [ ] Phase 5: Commit, push, post bead-based summary comment
```

### Phase 0: Prerequisites

Verify `bd` is available: run `bd --version`. If it fails, stop and
tell the user: "beads CLI (`bd`) is required but not found. Install
beads and run `bd init` in the target project."

### Phase 1: Setup

1. **Identify the PR.** Use `$ARGUMENTS` if provided, otherwise determine
   from context or ask.

2. **Read all unresolved comments:** `list <pr-number> --unacked`.
   If none exist, report and stop.

3. **Query beads for prior review findings.** Check if a review-pr run
   previously created beads for this PR:

   ```bash
   bd list --label "pr-review,pr:<number>" --json
   ```

   If a review bead exists, load all child findings:

   ```bash
   bd list --parent <review-bead-id> --json
   ```

   This provides full context from prior review-pr runs without
   re-deriving from PR comment text.

4. **Cross-reference.** Match GitHub PR comments against existing finding
   beads via `external-ref` URLs. Identify:
   - Comments that align with existing findings (human flagged same thing)
   - Comments that are new (not captured by review-pr)
   - Findings with no corresponding reviewer comment (bot-only findings)

5. **Gather review history.** Fetch all prior reviews and comments
   to understand the full conversation context:

   ```bash
   gh api repos/{owner}/{repo}/pulls/<number>/reviews
   gh api repos/{owner}/{repo}/pulls/<number>/comments
   ```

   Note which review round this is (first review, re-review after
   fixes, etc.) and whether previously flagged issues were resolved.
   Pass this context to sub-agents in Phase 3 so they understand
   what was already attempted.

6. **Locate the worktree.** Worktrees are in the sibling
   `<repo>_worktrees/` directory.
   - **git:** Run `git worktree list` and check whether one exists for
     the PR's branch. If one matches, `cd` into it and verify with
     `git branch --show-current`.
   - **jj:** Verify your working directory is under a `_worktrees/`
     sibling directory using `case "$(pwd)" in *_worktrees/*) ...`.
     Do NOT rely on `jj workspace list` output to identify the
     current workspace (jj 0.39+ has no `(current)` marker).
   If no worktree matches, ask the user whether to create one.

   **MUST** use an existing worktree if one matches.

### Phase 2: Categorize, clarify, and confirm

This phase has three distinct steps. Do NOT combine them.

**Step 2a — Categorize internally.** For each comment, assign a
**category**, **complexity**, and **model**. Do not present to the
user yet.

If a PR comment matches an existing finding bead (from the cross-reference
in Phase 1), note the finding bead ID for linking in Phase 3.

| Category     | Description                        | Action |
|--------------|------------------------------------|--------|
| **bug**      | Logic error, missing edge case     | Fix    |
| **style**    | Naming, formatting, lint issues    | Fix    |
| **feature**  | New functionality request          | Ask    |
| **design**   | Architecture, pattern, API shape   | Ask    |
| **question** | Clarification, "why did you..."    | Ask    |

| Complexity | Criteria                                    | Model  |
|------------|---------------------------------------------|--------|
| **low**    | Single file, mechanical change, obvious fix  | sonnet |
| **medium** | Few files, some judgment, clear approach     | sonnet |
| **high**   | Cross-cutting, architectural, needs context  | sonnet |

Escalate to **opus** when:

- The task is vague, under-specified, or has no clear precedent
- Design-related changes or questions (category **design**)
- The fix touches a significant fraction of the codebase

**Step 2b — Gather clarifications.** For every comment categorized as
feature, design, or question: present it to the user one at a time
with full context (comment text, file location, surrounding code).
Ask exactly one question per comment. Wait for the user's response
before presenting the next. Record each answer.

**Step 2c — Present plan for approval.** Show the full categorized
list to the user in a single summary:

- Each comment's ID, category, complexity, and recommended model
- For bug/style: the proposed fix approach
- For feature/design/question: the user's answer from Step 2b
  and the planned action

Ask the user to confirm or adjust before proceeding. Do NOT begin
implementation until the user approves.

### Phase 3: Implement

Dispatch each fix/response as a **sub-agent** using the Task tool
with the model from Phase 2. Each sub-agent should receive:

- The comment text and file location
- The category and what to do
- The related finding bead ID (if one exists from Phase 1 cross-reference)
- For bug/style: instructions to use TDD
- For feature/design/question: the user's guidance from Step 2b

**Concurrency limit: at most 3 sub-agents at a time.** If more than
3 fixes are independent, batch them into groups of 3 and wait for each
batch to finish before launching the next.

1. **Bug and style:** launch sub-agent with recommended model.
   - Sub-agent writes a failing test (when testable), implements
     fix, confirms pass.
   - After sub-agent completes:
     - If non-trivial, create a work bead:
       `bd create "Fix: <description>" --type task --deps "discovered-from:<finding-bead-id>" --silent`
     - Close the related finding bead: `bd update <finding-bead-id> --status closed`
     - Acknowledge: `ack <pr> <comment-id>`
   - Independent fixes MAY run as parallel sub-agents (up to 3).

2. **Feature, design, question:** launch sub-agent with recommended
   model and the user's guidance from Step 2b.
   - After sub-agent completes:
     - Create a work bead if applicable
     - Close the related finding bead if one exists
     - Acknowledge: `ack <pr> <comment-id>`

### Phase 4: Verify

Launch a **sonnet sub-agent** to run quality gates and fix any failures:

1. Sub-agent detects project type and runs appropriate quality gates:
   - **Detect:** Check for `Taskfile.yml`, `build.gradle`, `pyproject.toml`, `Cargo.toml`, `package.json`, etc.
   - **Run:** Execute project-specific commands for unit tests, integration tests, build, and lint
   - **Examples:**
     - Taskfile: `task test && task test:integration && task build && task lint`
     - Python: `pytest tests/ && pytest tests/integration/ && python -m build && ruff check`
     - Rust: `cargo test && cargo test --test integration && cargo build && cargo clippy`
     - Gradle: `./gradlew test integrationTest build check`
     - Node: `npm test && npm run test:integration && npm run build && npm run lint`
2. If failures: sub-agent reviews error → fixes → re-runs.
3. **Max 3 attempts.** If gates still fail after 3 rounds, sub-agent reports
   the remaining failures and stops. Present the failures to the user for guidance.
4. Do NOT proceed to Phase 4.5 until all gates pass (unit tests, integration tests, build, lint).

### Phase 4.5: Independent Review (Conditional)

**Trigger when ANY of these conditions apply:**

- 3+ comments addressed (high change volume)
- Any comment categorized as "high" complexity
- Any bug fix (category "bug")
- User explicitly requests review before shipping

Launch a **sonnet sub-agent** (independent context) to review. Sub-agent outputs
ONLY structured results (no explanations) to minimize token use:

**Sub-agent task:**

1. Read Phase 2 categorization (comment IDs, categories, user guidance)
2. Query beads for review state: `bd list --parent <review-bead-id> --json`
3. Run VCS diff to see actual changes (`git diff` or `jj diff`)
4. For EACH comment ID, output one line:

   ```text
   <comment-id>: PASS | FAIL: <reason-if-fail>
   ```

5. After all comments, output decision:

   ```text
   DECISION: SHIP | BLOCK
   BLOCK_REASON: <one-line-summary-if-blocked>
   ```

**Example output:**

```text
RC_123: PASS
RC_456: FAIL: Test added but doesn't cover edge case mentioned in comment
R_789: PASS
DECISION: BLOCK
BLOCK_REASON: RC_456 test incomplete
```

If DECISION is BLOCK, return to Phase 3 to address flagged issues, then re-run Phase 4 gates.
If DECISION is SHIP, proceed to Phase 5.

### Phase 5: Ship

1. **Commit** using the `commit-commands:commit` skill.
2. **Push** to the PR branch.
3. **Post summary comment** using the bead-based template:

   Write to `/tmp/pr-response-comment.md` and post via
   `comment <pr-number> --file /tmp/pr-response-comment.md`

   Template:

   ```markdown
   <!-- pr-review:<bead-id>:response -->
   ## <bead-id> — Review Response

   `bd list --parent <bead-id>`

   Addressed N/M · N deferred

   | Finding | Status |
   |---------|--------|
   | <bead-id> | Fixed |
   | <bead-id> | Deferred — reason |
   ```

   The HTML comment marker enables machine detection of response comments.

## Hard Constraints

| Constraint                   | Reason                    |
|------------------------------|---------------------------|
| **MUST NOT** close epic      | PR merge triggers closure |
| **MUST NOT** close issue     | PR merge triggers closure |
| **MUST NOT** merge the PR    | Reviewer's decision       |
| **MUST** use worktree        | Avoid branch conflicts    |
| **MUST** ask for feat/design | Require human judgment    |
| **MUST** use TDD for fixes   | Ensures correctness       |

## Notes

- `--unacked` filters by +1 reaction from the authenticated user.
- Prefer `--file` for multi-line comments (avoids shell escaping).
- MUST NOT create additional parsing or processing scripts.
- MUST use the comment ID formats provided in output.
