# Worktree Isolation Fix Design

Date: 2026-03-06

## Problem

Fix agents in the pr-review plugin have two failure modes:

1. **Fail to commit** -- fix-worker makes edits but never `git add`/`git commit`s,
   so the orchestrator's `git merge --no-ff <branch>` has nothing to merge.
2. **Edit wrong directory** -- agents use absolute paths from finding descriptions,
   writing to the base repo instead of their worktree.

Root causes:

- fix-worker's Process section has no commit step
- No agent has worktree-awareness instructions
- Default `EnterWorktree` nests worktrees inside `.claude/worktrees/` (confuses LSP)
- verification-runner has no context about what was fixed or why

## Design

### 1. Sibling Worktree Layout

Move worktrees from `.claude/worktrees/` (nested) to a sibling directory:

```text
<repo-root>/                    # e.g., fzymgc-house-skills/
<repo-root>_worktrees/          # e.g., fzymgc-house-skills_worktrees/
  fix-worker-abc123/
  verification-runner-def456/
```

Implemented via WorktreeCreate/WorktreeRemove hooks in `.claude/settings.json`.

### 2. Hook Scripts

`.claude/hooks/worktree-create.sh`:

- Derives `<repo>_worktrees/` path from repo root
- Detects VCS: creates `jj workspace add` (jj) or `git worktree add` (git)
- Installs lefthook in the new workspace
- Outputs the worktree path for the framework

`.claude/hooks/worktree-remove.sh`:

- Detects VCS: runs `jj workspace forget` (jj) or `git worktree remove` (git)
- Always removes the directory via `rm -rf` as final cleanup
- Cleans up empty parent directory if needed

### 3. Agent Prompt Changes

#### Environment Block (all 11 worktree-isolated agents)

Standard preamble for worktree awareness:

- Verify `pwd` and `git branch --show-current` on startup
- Use only relative paths
- Do not `cd` outside worktree directory

#### Commit Protocol (fix-worker + verification-runner)

After making changes, agents must commit before returning:

- `git add <specific-files>`
- `git commit -m "fix(<finding-id>): <description>"`
- `git log --oneline -1` to confirm

verification-runner uses `fix(lint): <description>` and only commits if it
made changes (lint auto-fixes).

#### Review Agents (9 read-only)

Get Environment block only. No commit protocol (they don't modify files).

### 4. Verification Runner Enhancement

Current: blind "run lint/build/tests" with no fix context.

New: receives a **fix manifest** from the orchestrator containing:

- Problem statement (from finding)
- Proposed fix (from finding's suggested fix)
- Actual changes (from fix-worker's result: files changed + description)

Two verification tasks:

1. **Fix alignment** -- does each change address its stated problem?
2. **Quality gates** -- lint, build, tests pass?

Output includes per-finding alignment status + gate results.

### 5. Complexity-Based Model Selection for Verification

Orchestrator selects verification model based on batch complexity
(already known from Phase 3 triage):

| Batch complexity | Model |
|---|---|
| All mechanical/single-file | sonnet |
| Any cross-cutting/architectural/vague | opus |

### 6. Orchestrator Updates (address-findings SKILL.md)

- Phase 4 dispatch: standardize commit message format in agent prompt
- Phase 4b: update worktree paths to sibling directory convention
- Phase 5: pass fix manifest to verification-runner, select model by complexity
- Worktree cleanup: `git worktree remove <sibling-path>`

## Files Changed

| File | Change |
|---|---|
| `.claude/hooks/worktree-create.sh` | New: create worktree in sibling dir |
| `.claude/hooks/worktree-remove.sh` | New: remove worktree |
| `.claude/settings.json` | Add WorktreeCreate/WorktreeRemove hooks |
| `pr-review/agents/fix-worker.md` | Environment block, commit protocol |
| `pr-review/agents/verification-runner.md` | Environment block, fix manifest, alignment check, conditional commit |
| 9 review agent `.md` files | Environment block |
| `pr-review/skills/address-findings/SKILL.md` | Phases 4, 4b, 5 updates |
| `pr-review/skills/respond-to-comments/SKILL.md` | Worktree location refs |
| `CLAUDE.md` | Document sibling worktree convention |
