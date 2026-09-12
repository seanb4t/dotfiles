# VCS Detection Preamble

Standard startup procedure for agents and skills operating in
repositories that may use git or jj (Jujutsu).

## Steps

1. **Detect VCS:**

   ```bash
   USE_VCS=$( \
     if jj root >/dev/null 2>&1; then echo "jj"; \
     elif git rev-parse --git-dir >/dev/null 2>&1; then echo "git"; \
     else echo "none"; fi \
   )
   if [[ "$USE_VCS" == "none" ]]; then
     echo "STATUS: FAILED -- No VCS detected (not inside a jj or git repository)"
     exit 1
   fi
   ```

   - `jj root` succeeds in any jj workspace (including workspaces where `.jj/` is absent from the working directory).
   - `git rev-parse --git-dir` succeeds in git worktrees where `.git` is a file rather than a directory.
   - If the result is "none", the shell block above exits immediately. As a backup prose instruction: STOP and report
     STATUS: FAILED -- "No VCS detected (not inside a jj or git repository)"
2. **Verify location** *(worktree-isolated agents only — orchestrator
   skills running from the main repo root should skip this step):*

   > **Skills:** Skip this step. Step 2 is for worktree-isolated agents only.
   - jj: Check whether the working directory is under a worktree workspace
     (sibling `_worktrees/` directory) rather than the default workspace:

     ```bash
     _cwd=$(pwd -P 2>/dev/null) || _cwd=$(pwd)
     _parent_dir=$(basename "$(dirname "$_cwd")")
     _in_worktree=false
     case "$_parent_dir" in
       *_worktrees) _in_worktree=true ;;
     esac
     if [[ "$_in_worktree" != "true" ]]; then
       echo "STATUS: FAILED -- Operating in default workspace (direct parent '$_parent_dir' does not end in _worktrees). Dispatch to a worktree workspace instead."
       exit 1
     fi
     ```

     Worktree workspaces are created in a sibling `<repo>_worktrees/` directory.
     The check verifies that the **direct parent directory** ends with `_worktrees`,
     so a repo at `/home/user/code_worktrees/myrepo` (parent: `myrepo`) does not
     trigger a false positive.

     > **Known limitation:** The `*_worktrees` parent-directory check relies on the
     > naming convention established by the WorktreeCreate hook. A
     > **false-positive** (agent incorrectly thinks it's in a worktree)
     > occurs only if the agent's direct parent directory happens to end with
     > `_worktrees` for unrelated reasons — uncommon in practice. A
     > **false-negative** (agent incorrectly thinks it's in the default workspace
     > when it's actually in a worktree) occurs if the hook naming convention
     > changes — more dangerous, since the worktree check is skipped entirely.
     > This is an accepted trade-off since `jj workspace list` does not mark the
     > current workspace (jj 0.39+). A false-negative causes an unnecessary
     > `STATUS: FAILED` — the agent refuses to proceed. This is a **safe failure
     > mode**: no data corruption occurs, and the operator can retry after
     > correcting the naming convention. Note the asymmetry: this jj check is
     > **heuristic** (directory naming convention), while the git check in Step 2
     > is **authoritative** (branch name pattern matching `worktree/*`) and
     > provides a stronger guarantee.

     Do NOT rely on `jj workspace list` output to identify the current
     workspace; jj 0.39+ does not emit a `(current)` marker.
   - git:

     ```bash
     _branch=$(git branch --show-current 2>/dev/null) || {
       echo "STATUS: FAILED -- git branch check failed"; exit 1
     }
     [[ -z "$_branch" ]] && {
       echo "STATUS: FAILED -- detached HEAD in git worktree — expected branch worktree/*"; exit 1
     }
     case "$_branch" in
       worktree/*) ;; # Good — operating on a worktree branch
       *)
         echo "STATUS: FAILED -- On branch '$_branch', expected worktree/*"
         exit 1
         ;;
     esac
     ```

3. If anything looks wrong, STOP and report STATUS: FAILED

**CRITICAL — Read Before Proceeding:**

- Use ONLY relative paths for all file operations
- Do NOT `cd` outside your working directory
- Do NOT use absolute paths from diffs or PR metadata -- translate them
  to relative paths within your worktree

Use the detected VCS for all operations in this session. When jj is
detected, MUST use jj commands for ALL VCS operations — commits,
workspaces, rebases, status, etc. Never use mutating git commands
(`git commit`, `git worktree add`, `git checkout`) in jj repos.
Read-only git commands and `gh` CLI are safe.

Consult `pr-review/references/vcs-equivalence.md` for command equivalents.

## Orchestrator Contract

When a worktree-isolated agent reports `STATUS: FAILED` with a VCS
detection failure message:

1. **Do NOT retry** — VCS detection failure is deterministic. The
   worktree was created without proper VCS initialization.
2. **Log the failure** — include the agent name and worktree path.
3. **Clean up the worktree** — the worktree is unusable without VCS.
4. **Re-queue the finding** — mark FAILED with the VCS error detail.

Orchestrator skills (address-findings, review-pr) should check for
`STATUS: FAILED` in agent responses before attempting to parse VCS-specific
fields (WORKTREE_BRANCH, CHANGE_ID).

## Path Rules

- Use ONLY relative paths for all file operations
- Do NOT `cd` outside your working directory
- Do NOT use absolute paths from diffs or PR metadata -- translate them
  to relative paths within your worktree
