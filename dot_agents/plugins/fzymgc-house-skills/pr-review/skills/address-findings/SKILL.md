---
name: address-findings
description: >-
  Processes findings from review-pr by working through beads in the review
  epic. Use when the user asks to "address review findings", "fix review
  issues", "work through review beads", or "process review findings".
argument-hint: "[pr-number]"
allowed-tools:
  - Task
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - "Bash(test *)"
  - "Bash(git *)"
  - "Bash(jj st)"
  - "Bash(jj st *)"
  - "Bash(jj log *)"
  - "Bash(jj diff *)"
  - "Bash(jj root)"
  - "Bash(jj workspace *)"
  - "Bash(jj rebase *)"
  - "Bash(jj bookmark *)"
  - "Bash(jj git *)"
  - "Bash(jj undo)"
  - "Bash(jj undo *)"
  - "Bash(jj describe *)"
  - "Bash(jj edit *)"
  - "Bash(jj commit *)"
  - "Bash(gh *)"
  - "Bash(bd --version)"
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
  version: 1.0.0 # x-release-please-version
---

# Address Findings

## Contents

- [VCS Detection](#vcs-detection)
- [Phase 1: Load](#phase-1-load)
- [Phase 2: Analyze Dependencies](#phase-2-analyze-dependencies)
- [Phase 3: Triage](#phase-3-triage)
- [Phase 4: Fix Loop](#phase-4-fix-loop)
- [Phase 5: Verify](#phase-5-verify)
- [Phase 6: Ship](#phase-6-ship)
- [Hard Constraints](#hard-constraints)

## VCS Detection

Follow the procedure in `pr-review/references/vcs-detection-preamble.md` to
detect git vs jj and verify your location. Use `gh` CLI for GitHub
operations regardless of VCS.

Process findings from a `review-pr` run by working through beads in the
review epic. Findings are triaged, fixed by isolated agents in worktrees,
batch-reviewed, and closed.

**Read** `references/bd-reference.md` for the full `bd` CLI reference.

## Phase 1: Load

1. **Identify the PR.** Use `$ARGUMENTS` if provided, otherwise ask.

2. **Verify `bd`**: run `bd --version`. If it fails, stop and tell the
   user: "beads CLI (`bd`) is required but not found."

3. **Check out the PR branch.** Worktree-isolated agents inherit their base
   from the orchestrator's current HEAD — if you are on `main`, agents will
   not see PR-specific code.

   **Detect VCS first, then check out:**

   ```bash
   USE_VCS=$(if jj root >/dev/null 2>&1; then echo jj; elif git rev-parse --git-dir >/dev/null 2>&1; then echo git; else echo none; fi)
   if [[ "$USE_VCS" == "jj" ]]; then
     # jj repo (including colocated jj+git): never use git checkout
     jj git fetch || { echo "ERROR: jj git fetch failed"; exit 1; }
     BOOKMARK=$(gh pr view <number> --json headRefName --jq .headRefName) || { echo "ERROR: gh pr view failed"; exit 1; }
     [[ -n "$BOOKMARK" ]] || { echo "ERROR: headRefName was empty"; exit 1; }
     jj bookmark track "${BOOKMARK}@origin" 2>/dev/null  # track if not already local
     jj edit "$BOOKMARK" || { echo "ERROR: jj edit failed"; exit 1; }
     # Verify: @ is the target commit after jj edit
     jj log -r @ --no-graph -n 1
   else
     # git-only repo
     gh pr checkout <number>
     git branch --show-current
   fi
   ```

   If checkout fails:
   - **PR not found** (GraphQL/404 error): stop — "PR #N not found. Verify the number and try again."
   - **Dirty working tree**: commit or stash, then retry.
   - **jj git fetch failed**: network or auth error — report and stop.
   - **Empty bookmark**: `gh pr view` returned empty headRefName — report and stop.
   - **jj edit failed**: bookmark not found or revision error — report and stop.
   - **Other error**: report and stop.

   **Do NOT proceed on `main`.**

4. **Query the review epic:**

   ```bash
   bd list --label "pr-review,pr:<number>" --status open --json
   ```

   If no epic exists, stop: "No review findings for PR #N. Run `/review-pr <number>` first."

5. **Load all open findings:**

   ```bash
   bd list --parent <epic-id> --status open --json
   ```

   If none, report "All findings already addressed" and stop.

6. No manual worktree discovery needed — fix-worker agents create their own
   worktrees via `isolation: worktree`.

7. **Validate findings against PR branch HEAD.** For each finding, verify the
   referenced file and line range still exist and the code matches the review
   snapshot. Check current HEAD:

   ```bash
   git log --oneline -1   # git repos
   jj log -r @- --no-graph -n 1  # jj repos
   ```

   If code has changed since the review, close as stale:

   ```bash
   bd update <finding-id> --status closed
   bd comments add <finding-id> "Closed: finding is stale — code at \
     <path>:<line> has changed since review. Re-run /review-pr if needed."
   ```

   Report discarded findings to the user before continuing.

## Phase 2: Analyze Dependencies

Review all open findings and identify dependency relationships:

**File overlap** — Two findings touching the same file MUST be serialized.
Set a dependency so the higher-priority finding is addressed first. This is
critical for merge safety.

**Conceptual overlap** — A design finding and a bug finding about the same
component. Resolve the design finding first (it may change the fix approach).

**Severity ordering** — Critical findings block lower-severity findings in
the same file or area.

Encode relationships:

```bash
bd dep add <lower-priority> --depends-on <higher-priority>
```

The fix loop's "query ready findings" naturally respects the dependency
graph — a finding cannot be picked up while its dependencies are open.

## Phase 3: Triage

For each open finding, evaluate:

1. **Complexity** — Straightforward fix or requires judgment?
2. **Scope** — Mechanical tweak or design/contract shift?
3. **Deviation** — Follows existing patterns or introduces new ones?

**Auto-fixable** (no user input needed):

- Clear bug with an obvious correct fix
- Mechanical changes (formatting, naming, lint)
- Low deviation from existing code and patterns

**Needs human judgment** — present via `AskUserQuestion`:

- Fix requires a design or architectural choice
- Fix changes a spec, plan, or public contract
- Multiple valid approaches with meaningful trade-offs

For needs-human findings, use `AskUserQuestion` with concrete fix options,
a "(Recommended)" label when clear, a "Defer" option, and "Other" is
provided automatically.

**Model assignment:**

| Criteria | Model |
|---------------------------------------------------|--------|
| Single file, mechanical, obvious fix | sonnet |
| Few files, some judgment, clear approach | sonnet |
| Cross-cutting, architectural, needs context | sonnet |
| Vague, under-specified, no clear precedent | opus |
| Design changes requiring architectural judgment | opus |

**Deferral handling:** When the user chooses "Defer":

1. Add label: `bd update <finding-id> --add-label deferred`
2. Create deferred work bead with full context:

   ```bash
   bd create "<description>" --type task \
     --labels "deferred,aspect:<aspect>,from-pr:<number>" \
     --external-ref "https://github.com/{owner}/{repo}/pull/<number>" \
     --description "<context, file location, reason>" --silent
   ```

3. Link: `bd dep add <deferred-bead> --depends-on <finding-id> --type discovered-from`

## Phase 4: Fix Loop

**Before entering the loop**, verify branch and working tree state:

```bash
git branch --show-current   # MUST be the PR branch, NOT main (git)
git status --porcelain      # MUST be clean (git)
jj log -r @- --no-graph -n 1   # MUST show PR bookmark (jj)
jj st                          # MUST be clean (jj)
```

If on `main`, stop — you skipped step 3. If there are uncommitted changes,
commit them first. A clean working tree on the correct PR branch is required
before dispatching worktree-isolated agents.

Loop while open, non-deferred findings remain:

1. **Query ready findings** (deps all closed):

   ```bash
   bd list --parent <epic-id> --status open --json
   ```

   Filter to findings whose dependencies are all closed.

2. **Pick up to 3** ready findings. No same-file overlap in a batch.

3. **Create work bead** per finding:

   ```bash
   bd create "Fix(<finding-id>): <short desc>" \
     --type task --parent <epic-id> \
     --description "<work to be done>" \
     --deps "blocks:<finding-id>" --silent
   ```

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
     Report STATUS, VCS, FILES_CHANGED, DESCRIPTION, WORKTREE_BRANCH (git) or CHANGE_ID (jj).
     VCS must be "git" or "jj" to indicate which integration method to use.
     Do NOT close or update any beads.
   ```

   Note: FILE_LOCATION **must** use a relative path. Strip any absolute
   prefix before dispatching.

5. **Collect results** from each agent: STATUS, VCS, FILES_CHANGED,
   DESCRIPTION, WORKTREE_BRANCH (git) or CHANGE_ID (jj).

   If `VCS` is missing from the fix-worker response:

   The Task framework returns `worktreePath` in isolation metadata
   when `isolation: worktree` is used. Use this as `<worktree-path>`
   in the steps below. If unavailable, reconstruct from the worktree
   naming convention: `<repo>_worktrees/<worktree-name>`.

   0. Verify worktree path exists: `test -d <worktree-path>`. If already
      removed:
      - If WORKTREE_BRANCH or CHANGE_ID is present, use it directly.
      - If both WORKTREE_BRANCH and CHANGE_ID are absent, mark FAILED
        immediately — the fix-worker result is unrecoverable. Clean up the
        worktree directory if it still exists (`rm -rf <worktree-path>`).
        Add a bead comment: "fix-worker returned no VCS, WORKTREE_BRANCH,
        or CHANGE_ID — result is unrecoverable". Re-queue the finding.
      Only fall through to inference if the path is accessible.

   1. Detect VCS in the main repo:
      `if jj root > /dev/null 2>&1; then echo jj; elif git rev-parse --git-dir > /dev/null 2>&1; then echo git; else echo none; fi`
      — if `none`, mark FAILED and skip integration.
      Clean up the worktree directory: `rm -rf <worktree-path>`.
      Add a bead comment with the failure details:

      ```bash
      _fail_msg="STATUS: FAILED — VCS detection returned 'none'. Worktree directory removed."
      if test -d .jj; then
        _fail_msg="$_fail_msg WARNING: .jj/ exists — orphaned jj workspace metadata may remain. Run: jj workspace forget <name>"
      fi
      bd comments add <work-bead-id> "$_fail_msg"
      ```

   2. git: `git -C <worktree-path> branch --show-current`
      — if the command fails or returns empty (e.g., detached HEAD), mark FAILED.
   3. jj: First verify `test -d <worktree-path>` — if the directory was already
      removed (e.g., by PARTIAL cleanup), mark FAILED with message:
      'VCS inference failed: worktree directory already removed during prior cleanup'.
      Otherwise run `cd <worktree-path> && jj log -r @- --no-graph -T 'change_id.short(8)'`
      — reads the committed fix (parent of working copy). If jj log fails, mark FAILED
      with message: 'VCS inference failed: jj log error: \<error output\>'.
   4. Log warning: "fix-worker omitted VCS field — inferred \<vcs\>"

### Phase 4b: Integrate Fix Commits

Integration method depends on VCS:

| VCS | Integration | Identifier | Cleanup |
|-----|-------------|------------|---------|
| git | `git cherry-pick` | WORKTREE_BRANCH | `git worktree remove` |
| jj | `jj rebase` + `jj bookmark set` | CHANGE_ID | `jj workspace forget` + `rm -rf` |

#### STATUS: PARTIAL handling

Treat PARTIAL the same as FAILED: skip integration, add a bead comment
noting the partial fix, and re-queue the finding for the next round.

```bash
bd comments add <finding-bead-id> "fix-worker reported PARTIAL: <DESCRIPTION>. Re-queued for next round."
```

Do NOT attempt to cherry-pick or rebase a PARTIAL result.

**Cleanup:** Even though integration is skipped, the fix-worker's worktree
must be cleaned up to prevent resource leaks:

- git: `git worktree remove ../<repo>_worktrees/<worktree-name> || { echo "WARNING: git worktree remove failed" >&2; git worktree prune; }`
- jj: forget workspace then remove directory:

  ```bash
  jj workspace forget worktree-<name> || echo "WARNING: jj workspace forget failed" >&2
  rm -rf ../<repo>_worktrees/<worktree-name> || echo "WARNING: rm failed" >&2
  ```

#### Git repos

For each FIXED result, in dependency order:

1. Identify the fix commit: `git log --oneline <worktree-branch> -1`
2. Cherry-pick onto the PR branch: `git cherry-pick <commit-sha>`
3. If conflict: abort (`git cherry-pick --abort`), clean up (`git worktree
   remove ../<repo>_worktrees/<worktree-name>`), mark FAILED, add bead comment,
   re-queue for next round.
4. Clean up: `git worktree remove ../<repo>_worktrees/<worktree-name>`

Same-file findings serialized in Phase 2 prevent most conflicts.

#### Jj repos

For each FIXED result (fix worker reports CHANGE_ID instead of WORKTREE_BRANCH):

1. Capture pre-rebase state:

   ```bash
   _pre_rebase_tip=$(jj log -r <pr-bookmark> --no-graph -T 'change_id.short(8)')
   ```

2. Rebase the fix onto the PR bookmark:

   ```bash
   jj rebase -r <change-id> -o <pr-bookmark>
   ```

   If rebase returns non-zero: do NOT run `jj undo` — nothing was committed.
   Clean up workspace (step 5), mark FAILED, add bead comment, re-queue.

3. Check for conflicts:

   ```bash
   _jj_log_failed=false
   _conflict_check=$(jj log -r <change-id> --no-graph -T 'if(conflict, "CONFLICT", "OK")') || _jj_log_failed=true
   if [[ "$_jj_log_failed" == true ]]; then
     # jj log failed — clean up workspace (step 5), mark FAILED, re-queue
     bd comments add <work-bead-id> "jj log -r <change-id> failed after rebase — cannot verify conflict state. Re-queued."
     # <cleanup step 5>
     # continue to next finding
   elif echo "$_conflict_check" | grep -q 'CONFLICT'; then
     # Conflict detected — undo the rebase
     jj undo || {
       # jj undo failed — STOP and escalate
       bd comments add <work-bead-id> "jj undo failed to revert conflicted rebase — manual recovery required."
       # STOP: report STATUS: FAILED. Do NOT re-queue; escalate to user.
     }
     _post_undo_tip=$(jj log -r <pr-bookmark> --no-graph -T 'change_id.short(8)')
     if [[ "$_post_undo_tip" != "$_pre_rebase_tip" ]]; then
       # jj undo did not restore expected state — STOP and escalate
       bd comments add <work-bead-id> "jj undo did not restore expected state — manual recovery required."
       # <cleanup step 5>
       # STOP: report STATUS: FAILED. Do NOT re-queue; escalate to user.
     fi
     # Clean up workspace (step 5), mark FAILED, re-queue
     # continue to next finding
   else
     # No conflict — proceed to step 4
     :
   fi
   ```

   If `jj log` returns non-zero: clean up workspace (step 5), mark FAILED, add bead
   comment: "jj log -r \<change-id\> failed after rebase — cannot verify conflict
   state". Re-queue for next round.

   If conflict detected: run `jj undo` to revert. If `jj undo` fails, STOP and report
   STATUS: FAILED — "jj undo failed to revert conflicted rebase — manual
   recovery required". Do NOT re-queue; escalate to user.
   Verify:

   ```bash
   _post_undo_tip=$(jj log -r <pr-bookmark> --no-graph -T 'change_id.short(8)')
   ```

   If `_post_undo_tip != _pre_rebase_tip`, STOP: "jj undo did not restore
   expected state". Clean up workspace (step 5). Mark FAILED. Do NOT
   re-queue; escalate to user.

4. Update the bookmark:

   ```bash
   jj bookmark set <pr-bookmark> -r <change-id>
   ```

   If bookmark set fails:

   1. Run `jj undo` once — reverts the successful rebase from step 2.
      If `jj undo` fails, STOP: "jj undo failed to revert rebase — manual
      recovery required".

      **Why only one undo?** jj's op log records only *successful* operations.
      A failed `jj bookmark set` leaves no op-log entry, so there is nothing
      to undo for the failure. The single undo targets the successful rebase.

   2. Verify:

      ```bash
      _post_undo_tip=$(jj log -r <pr-bookmark> --no-graph -T 'change_id.short(8)')
      ```

      If `_post_undo_tip != _pre_rebase_tip`, STOP: "jj undo did not restore
      expected state".

   3. Clean up workspace (step 5). Mark FAILED, add bead comment, re-queue.

5. Forget the workspace and remove the directory:

   Derive `<name>` from the Task isolation metadata `worktreePath`:
   `basename <worktreePath>`. The jj workspace name is `worktree-<name>`.
   For example, if worktreePath is `../repo_worktrees/agent-abc12345`,
   then `<name>` is `agent-abc12345` and the workspace name is
   `worktree-agent-abc12345`.

   ```bash
   jj workspace forget worktree-<name> || echo "WARNING: jj workspace forget failed" >&2
   rm -rf ../<repo>_worktrees/<worktree-name> || echo "WARNING: rm -rf worktree directory failed" >&2
   ```

   If `jj workspace forget` fails, log a warning but proceed with `rm -rf`.
   If `rm -rf` fails, log a warning — the directory leak is detectable.

#### Post-batch verification

After all commits in a batch are integrated, verify clean state before the
next loop iteration:

```bash
git status --porcelain   # git repos
jj st                    # jj repos
```

Never dispatch new fix-worker agents with uncommitted changes in the main
working tree.

### Phase 4c: Review Gate

Dispatch a review-gate agent to validate fixes.
Generate the diff before dispatching. For jj repos, capture the
pre-batch bookmark tip before Phase 4b with
`jj log -r <pr-bookmark> --no-graph -T 'change_id.short(8)'`:

- git: `git diff <before-sha>..HEAD`
- jj: `jj diff --from <pre-batch-bookmark-tip> --to <pr-bookmark>`

```text
subagent_type: "review-gate"
model: sonnet
prompt: |
  FINDING_IDS: <comma-separated>
  Review the following changes against the original findings.
  <VCS diff of integrated changes>
  Return per-finding: PASS | FAIL: <reason>
```

- **PASS**: close work bead (`bd update <work-id> --status closed`)
  then close finding (`bd update <finding-id> --status closed`)
- **FAIL**: add comment (`bd comments add <finding-id> "Review failed: <reason>"`),
  re-queue for next round

Max 2 retries per finding. After 2 failures, escalate to user.

## Phase 5: Verify

Build a **fix manifest** from the collected fix-worker results:

| Finding | Problem | Proposed Fix | Actual Changes |
|---------|---------|--------------|----------------|
| bead-id | from finding description | suggested fix | files + description from fix-worker |

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
  ## Fix Manifest

  <fix manifest table from above>

  Validate fix alignment and run quality gates.
  Report per-finding alignment AND gate status.
```

**Parse verification-runner output:** The verification-runner uses the same
VCS field protocol as fix-worker (see Phase 4 step 5). These identifiers are
informational — the primary result field is `STATUS`.

- **Any MISALIGNED finding**: treat as review-gate FAIL, re-queue
- **Gate FAIL**: report failure details to user. Do NOT proceed to Phase 6.
- **All ALIGNED + gates PASS**: proceed.

## Phase 6: Ship

1. **Commit** changes:
   - git repos: Use the `commit-commands:commit` skill.
   - jj repos: All fixes are already committed. Skip unless the working copy
     has uncommitted manual edits — then run
     `jj commit -m "fix: address review findings for PR #<number>"`.
2. **Push** to the PR branch: `git push` (or `jj git push -b <pr-bookmark>` in jj repos)
3. **Post summary comment** on the PR:

   ```bash
   gh pr comment <number> --body-file /tmp/review-response.md
   ```

   Template:

   ```markdown
   <!-- address-findings:<epic-id>:response -->
   ## Review Response

   Fixed N | Deferred N | Failed N

   | Finding | Status | Work |
   |---------|--------|------|
   | <finding-id> | Fixed | <work-bead-id> |
   | <finding-id> | Deferred | <deferred-bead-id> |
   | <finding-id> | Failed (escalated) | -- |
   ```

## Hard Constraints

| Constraint | Reason |
|--------------------------------------|---------------------------|
| **MUST NOT** close the review epic | PR merge triggers closure |
| **MUST NOT** merge the PR | Reviewer's decision |
| **MUST** use `AskUserQuestion` for human judgment | Structured input |
| **MUST** filter `--status open` in all bead queries | Skip handled findings |
| **MUST NOT** let sub-agents close beads | Orchestrator owns lifecycle |
| **MUST** use long flags for all `bd` commands | Clarity for agents |
| **MUST** validate findings against HEAD before fixing | Prevent stale false positives |
| **MUST** commit between fix-worker rounds | Prevent worktree branch corruption |
| **MUST** verify clean working tree before dispatching agents | Prevent data loss |
| **MUST** be on the PR branch before dispatching agents | Worktrees inherit base from HEAD |
| **MUST NOT** proceed with fixes while on `main` | Agents would work against wrong code |
