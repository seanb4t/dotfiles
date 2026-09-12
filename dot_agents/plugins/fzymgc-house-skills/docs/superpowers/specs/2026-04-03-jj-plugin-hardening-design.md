# jj Plugin Hardening

Date: 2026-04-03

## Problem

The jj plugin has accumulated several operational gaps since its initial
PR #31 merge:

1. **Pager hangs** -- SKILL.md examples omit `--no-pager`, so agents in
   environments without `paginate = "never"` config hang on jj output.
2. **Parallel agent collisions** -- no documented rule prevents dispatching
   multiple agents against the same jj working copy, which causes `@`
   conflicts (observed in holomush session 2026-04-03).
3. **`jj undo` confusion** -- the op-log-only-records-successful-ops
   gotcha is documented in `references/jj-reference.md` but missing from
   the main SKILL.md where agents actually read it.
4. **Stale jjagent memory** -- `memory/reference_jjagent.md` references a
   disabled plugin we don't use; it wastes context and confuses future
   sessions.
5. **Missing test assertion** -- `test_jj_workspace_not_in_list` (bead
   `qpw.5`) never asserts `returncode`, so the test passes even when the
   hook exits with code 1.
6. **Conflict marker version** -- SKILL.md documents jj 0.39+ format
   without noting it's version-specific.
7. **Session-start skill loading** -- already fixed earlier today; the
   `session-start-jj-detect` hook now includes a directive to load the
   jujutsu skill.

## Scope

All changes are within the `jj/` plugin directory plus one memory file
deletion. No architectural changes. No new files except tests.

### In scope

- SKILL.md content fixes (items 1-3, 6)
- `session-start-jj-detect` hook output (item 1: `--no-pager` in quick
  reference examples)
- `memory/reference_jjagent.md` deletion + MEMORY.md update (item 4)
- `.claude/hooks/tests/test_worktree_remove.py` assertion fix (item 5)
- `.claude/hooks/worktree-remove` logic fix if needed for item 5

### Out of scope

- Historical design docs in `docs/plans/2026-03-07-jj-vcs-support*.md`
  (decision: leave as-is)
- jjagent fork/upstream fix (separate feature, tracked elsewhere)
- `jj fix` config generator (bead `n7l`, separate feature)
- Guard hook changes (already solid)
- Worktree create/remove hooks (already VCS-aware)

## Design

### 1. `--no-pager` safety

**SKILL.md Agent Environment Rules** -- add rule:

> You MUST use `--no-pager` on every `jj` command, or pass
> `--config ui.paginate=never`. Agent environments cannot interact
> with pagers.

No changes to allowed-tools needed -- `--no-pager` is a flag, not a
subcommand, so `Bash(jj log *)` already covers `jj --no-pager log`.

**session-start-jj-detect hook** -- add `--no-pager` to all `jj`
commands in the quick reference section output.

### 2. Parallel agent workspace collision warning

**SKILL.md Agent Environment Rules** -- new rule:

> You MUST NOT dispatch multiple agents against the same jj working
> copy. Each parallel agent MUST work in its own workspace created via
> `jj workspace add`. The orchestrating skill is responsible for
> workspace creation before agent dispatch and cleanup after.

Cross-reference the "Agent Fan-Out" section in
`references/workflows-reference.md` which already has the full pattern.

### 3. `jj undo` op-log semantics

**SKILL.md "Abandon, Undo, and Restore" section** -- add warning block
after the `jj undo` example:

> **Warning:** The op log only records successful operations. A failed
> command leaves no trace. `jj undo` always targets the most recent
> *successful* operation -- do NOT "undo twice" to account for a
> failure. See `references/jj-reference.md` for the full op log
> reference.

### 4. Remove jjagent memory

- Delete `memory/reference_jjagent.md`
- Remove its line from `memory/MEMORY.md`
- Remove SKILL.md line 485-486 "session-level change management" hint
  (the only indirect jjagent reference in active code)

### 5. Fix `test_jj_workspace_not_in_list` assertion

Two changes needed:

**`.claude/hooks/worktree-remove`** -- in `_jj_cleanup()`, when
`jj workspace forget` fails because the workspace wasn't in the list,
return `False` (not a metadata leak) instead of `True`.

**`.claude/hooks/tests/test_worktree_remove.py`** -- add
`assert result.returncode == 0` to the test, confirming the hook
treats unregistered-workspace cleanup as a non-error.

### 6. Conflict marker version note

**SKILL.md "Resolving Conflicts" section** -- add one-line note:

> The markers shown below are the jj 0.39+ format. Older versions use
> a simpler `+++++++`/`-------` format without `%%%%%%%` diff sections.

### 7. Session-start skill-load directive

Already implemented. The `session-start-jj-detect` hook now outputs a
`## REQUIRED: Load jj skill` section instructing Claude to invoke
`Skill(jj:jujutsu)` before its first response. Test added and passing.

## Commit Plan

One branch, atomic commits per logical change:

1. `fix(jj): add --no-pager safety to SKILL.md and session-start hook`
2. `fix(jj): add parallel agent workspace collision warning`
3. `fix(jj): document jj undo op-log semantics in SKILL.md`
4. `chore(jj): remove stale jjagent memory reference`
5. `fix(jj): add returncode assertion to workspace removal test`
6. `docs(jj): note conflict marker format is version-specific`
7. `feat(jj): load jujutsu skill at session start` (already done)

## Verification

- `uv run --with pytest pytest jj/hooks/tests/ -v` -- all tests pass
- `uv run --with pytest pytest .claude/hooks/tests/ -v` -- worktree
  tests pass with new assertion
- `lefthook run pre-commit --all-files` -- no lint failures
- Manual: start a Claude Code session in a jj repo, confirm skill
  auto-loads
