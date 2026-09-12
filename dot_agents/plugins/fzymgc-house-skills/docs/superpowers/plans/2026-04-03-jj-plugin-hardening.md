# jj Plugin Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix operational gaps in the jj plugin -- pager safety, parallel agent collisions, undo semantics, stale references, and a missing test assertion.

**Architecture:** All changes are content/documentation fixes in the `jj/` plugin directory plus one memory cleanup and one test fix in `.claude/hooks/`. No new files, no architectural changes.

**Tech Stack:** Python (hooks/tests), Markdown (SKILL.md, references), uv + pytest

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `jj/skills/jujutsu/SKILL.md` | Modify | Add `--no-pager` rule, parallel agent warning, undo semantics, conflict version note, remove jjagent hint |
| `jj/hooks/session-start-jj-detect` | Modify | Fix `-d` → `-o` rebase flag, add `--no-pager` to quick ref |
| `jj/hooks/tests/test_session_start_jj_detect.py` | Modify | Add test for rebase flag correctness |
| `.claude/hooks/worktree-remove` | Modify | Fix `_jj_cleanup` return for unregistered workspaces |
| `.claude/hooks/tests/test_worktree_remove.py` | Modify | Add returncode assertion to `test_jj_workspace_not_in_list` |
| `memory/reference_jjagent.md` (user memory) | Delete | Remove stale jjagent reference |
| `memory/MEMORY.md` (user memory) | Modify | Remove jjagent line |

---

### Task 1: Add `--no-pager` safety rule to SKILL.md

**Files:**

- Modify: `jj/skills/jujutsu/SKILL.md:88-102` (Agent Environment Rules section)

- [ ] **Step 1: Add `--no-pager` rule to Agent Environment Rules**

In `jj/skills/jujutsu/SKILL.md`, in the "Agent Environment Rules" section (after line 92, the existing `jj git fetch` rule), add a new rule:

```markdown
- You MUST pass `--no-pager` on every `jj` command (e.g., `jj --no-pager log`).
  Agent environments cannot interact with pagers. Alternatively, pass
  `--config ui.paginate=never` as a flag.
```

- [ ] **Step 2: Verify SKILL.md renders correctly**

Read the modified section to confirm formatting is clean and the new rule integrates with the existing list.

- [ ] **Step 3: Commit**

```text
jj commit -m "fix(jj): add --no-pager safety rule to SKILL.md Agent Environment Rules"
```

---

### Task 2: Fix rebase flag and add `--no-pager` to session-start hook

**Files:**

- Modify: `jj/hooks/session-start-jj-detect:138-167` (quick reference output)
- Modify: `jj/hooks/tests/test_session_start_jj_detect.py` (add rebase flag test)

- [ ] **Step 1: Fix the rebase flag in session-start hook**

In `jj/hooks/session-start-jj-detect`, line 152, change:

```python
        "  git rebase --onto D S → jj rebase -s S -d D (use -d not --onto in jj 0.25+)",
```

to:

```python
        "  git rebase --onto D S → jj rebase -s S -o D (-d is deprecated; use -o / --onto)",
```

- [ ] **Step 2: Add `--no-pager` to jj commands in the quick reference**

In the same file, update the quick reference jj commands to include `--no-pager` where applicable. Change the header area (after the VCS Policy section, around line 134) to add a note:

```python
        "You MUST pass --no-pager on every jj command in agent environments.",
        "",
```

Insert this after line 134 (`"You MAY use git plumbing commands (rev-parse, ls-files) and gh CLI.",`).

Also update the rebase line in the "Remote operations" section at line 161:

```python
        "  git pull    → jj git fetch (then jj rebase -o BOOKMARK if needed)",
```

(Change `-d BOOKMARK` to `-o BOOKMARK`.)

- [ ] **Step 3: Add test for rebase flag correctness**

In `jj/hooks/tests/test_session_start_jj_detect.py`, add a test in `TestOutputFormat`:

```python
    def test_rebase_flag_uses_onto(self, jj_repo: Path) -> None:
        """Rebase quick reference must use -o (not deprecated -d)."""
        result = run_hook(str(jj_repo))
        assert "-o D" in result.stdout or "--onto" in result.stdout
        assert "-d D" not in result.stdout
```

- [ ] **Step 4: Run tests**

Run: `uv run --with pytest pytest jj/hooks/tests/test_session_start_jj_detect.py -v`
Expected: All tests pass including new `test_rebase_flag_uses_onto`.

- [ ] **Step 5: Commit**

```text
jj commit -m "fix(jj): correct rebase flag (-d → -o) and add --no-pager note to session-start hook"
```

---

### Task 3: Add parallel agent workspace collision warning to SKILL.md

**Files:**

- Modify: `jj/skills/jujutsu/SKILL.md:88-110` (Agent Environment Rules section)

- [ ] **Step 1: Add parallel agent rule**

In `jj/skills/jujutsu/SKILL.md`, after the existing agent rules (after line 102, before the interactive commands table), add:

```markdown
**Parallel agent safety:**

- You MUST NOT dispatch multiple agents against the same jj working copy — they
  will fight over `@` and cause orphaned branches. Each parallel agent MUST work
  in its own workspace created via `jj workspace add`. The orchestrating skill
  is responsible for workspace creation before dispatch and cleanup after.
  See `references/workflows-reference.md` "Agent Fan-Out" for the full pattern.
```

- [ ] **Step 2: Verify formatting**

Read the modified section to confirm the new block integrates cleanly.

- [ ] **Step 3: Commit**

```text
jj commit -m "fix(jj): add parallel agent workspace collision warning to SKILL.md"
```

---

### Task 4: Document jj undo op-log semantics in SKILL.md

**Files:**

- Modify: `jj/skills/jujutsu/SKILL.md:213-225` (Abandon, Undo, and Restore section)

- [ ] **Step 1: Add undo warning**

In `jj/skills/jujutsu/SKILL.md`, after the `jj undo` code block (after line 220, `jj undo`), add:

```markdown
**Warning — op log semantics:** The op log only records **successful** operations.
A failed jj command leaves no trace in the op log (unlike git's reflog). `jj undo`
always targets the most recent *successful* operation — do NOT "undo twice" to
account for a failure. If you need to recover from a bad state, use
`jj op log` to find the right operation ID, then `jj op restore <op-id>`.
See `references/jj-reference.md` for the full op log reference.
```

- [ ] **Step 2: Verify formatting**

Read the modified section to confirm the warning integrates cleanly between the code block and the `jj split` note.

- [ ] **Step 3: Commit**

```text
jj commit -m "fix(jj): document jj undo op-log semantics in SKILL.md"
```

---

### Task 5: Remove stale jjagent references

**Files:**

- Delete: `memory/reference_jjagent.md` (path: `/Users/sean/.claude/projects/-Volumes-Code-github-com-fzymgc-house-fzymgc-house-skills/memory/reference_jjagent.md`)
- Modify: `memory/MEMORY.md` (path: `/Users/sean/.claude/projects/-Volumes-Code-github-com-fzymgc-house-fzymgc-house-skills/memory/MEMORY.md`)
- Modify: `jj/skills/jujutsu/SKILL.md:485-486` (See Also section, jjagent hint)

- [ ] **Step 1: Delete memory file**

```bash
rm /Users/sean/.claude/projects/-Volumes-Code-github-com-fzymgc-house-fzymgc-house-skills/memory/reference_jjagent.md
```

- [ ] **Step 2: Remove jjagent line from MEMORY.md**

In `/Users/sean/.claude/projects/-Volumes-Code-github-com-fzymgc-house-fzymgc-house-skills/memory/MEMORY.md`, line 24, change:

```markdown
- `jj` plugin: jujutsu skill + /jj-init command; complements jjagent plugin (session-level change mgmt)
```

to:

```markdown
- `jj` plugin: jujutsu skill + /jj-init command
```

- [ ] **Step 3: Remove session-level change management hint from SKILL.md**

In `jj/skills/jujutsu/SKILL.md`, remove lines 485-486:

```markdown
- For session-level change management (splitting, describing, inserting changes),
  use `jj commit`, `jj describe`, and `jj new` directly.
```

These lines are the last indirect jjagent reference. The commands they mention are already documented earlier in the skill.

- [ ] **Step 4: Commit**

```text
jj commit -m "chore(jj): remove stale jjagent memory and SKILL.md references"
```

Note: This commit only covers the `jj/skills/jujutsu/SKILL.md` change in the repo. The memory file changes are outside the repo and don't need a commit.

---

### Task 6: Fix `test_jj_workspace_not_in_list` assertion

**Files:**

- Modify: `.claude/hooks/worktree-remove:40-99` (`_jj_cleanup` function)
- Modify: `.claude/hooks/tests/test_worktree_remove.py:410-433` (`test_jj_workspace_not_in_list`)

- [ ] **Step 1: Fix `_jj_cleanup` return value for unregistered workspaces**

In `.claude/hooks/worktree-remove`, the `_jj_cleanup` function currently returns `True` (metadata leak) whenever `jj workspace forget` fails — even when the workspace wasn't listed. An unregistered workspace can't leak metadata.

Change the logic: after the `forget_result` check (lines 87-97), differentiate between "workspace was listed but forget failed" (true leak) and "workspace was not listed and forget failed" (no leak).

Replace lines 84-97 with:

```python
    # Track whether workspace was listed
    ws_was_listed = ws_list_result.returncode != 0 or ws_with_colon in ws_list or jj_workspace in ws_list

    forget_result = run_cmd(
        ["jj", "--no-pager", "workspace", "forget", jj_workspace], cwd=repo_root
    )
    if forget_result.returncode != 0:
        jj_err = sanitize_for_output(forget_result.stderr.strip()[:500])
        if ws_was_listed:
            # Workspace was registered but forget failed — real metadata leak
            print(
                f"ERROR: jj workspace forget failed for "
                f"{sanitize_for_output(jj_workspace)}: {jj_err}; "
                f"workspace directory will still be removed "
                f"(run 'jj workspace forget {sanitize_for_output(jj_workspace)}' "
                f"manually to clean up)",
                file=sys.stderr,
            )
            return True  # jj_forget_failed — metadata leak
        else:
            # Workspace was not listed — forget failure is expected, not a leak
            print(
                f"INFO: jj workspace forget failed for "
                f"{sanitize_for_output(jj_workspace)} (workspace was not registered): "
                f"{jj_err}",
                file=sys.stderr,
            )
            return False  # no metadata leak

    return False  # success
```

This requires tracking `ws_was_listed` before the forget call. The variable needs to be set based on the `ws_list_result` check that already happens above (lines 57-82). Add the `ws_was_listed` assignment after the existing workspace list checking block, at line 83 (before `forget_result`):

```python
    # Determine if workspace appeared in the list (or if listing failed, assume it might be listed)
    ws_was_listed = (
        ws_list_result.returncode != 0  # list failed — can't confirm absence
        or ws_with_colon in (ws_list_result.stdout or "")
        or jj_workspace in (ws_list_result.stdout or "")
    )
```

Note: `ws_list` variable is only set when `ws_list_result.returncode == 0`, so use `ws_list_result.stdout` directly for the `ws_was_listed` check to avoid NameError when listing failed.

- [ ] **Step 2: Add returncode assertion to the test**

In `.claude/hooks/tests/test_worktree_remove.py`, in `test_jj_workspace_not_in_list` (line 410), add the assertion after the existing stderr checks (line 425):

```python
            # Hook should succeed (unregistered workspace is not a metadata leak)
            assert result.returncode == 0
```

Add this between the existing `assert "not found" in result.stderr or "INFO" in result.stderr` line and the `assert not worktree_path.exists()` line.

- [ ] **Step 3: Run worktree tests**

Run: `uv run --with pytest pytest .claude/hooks/tests/test_worktree_remove.py -v`
Expected: All tests pass, including `test_jj_workspace_not_in_list` now asserting returncode == 0.

- [ ] **Step 4: Commit**

```text
jj commit -m "fix(jj): return success for unregistered workspace cleanup in worktree-remove"
```

---

### Task 7: Add conflict marker version note to SKILL.md

**Files:**

- Modify: `jj/skills/jujutsu/SKILL.md:424-430` (Conflict Handling section)

- [ ] **Step 1: Add version note**

In `jj/skills/jujutsu/SKILL.md`, before the conflict marker list (line 425, "Open the conflicted file..."), add:

```markdown
1. Open the conflicted file and resolve the conflict markers (jj 0.39+ format;
   older versions use a simpler format without `%%%%%%%` diff sections):
```

This replaces the existing line 425:

```markdown
1. Open the conflicted file and resolve the conflict markers (jj 0.39 format):
```

- [ ] **Step 2: Verify formatting**

Read the section to confirm the note reads naturally.

- [ ] **Step 3: Commit**

```text
jj commit -m "docs(jj): note conflict marker format is jj 0.39+ specific"
```

---

### Task 8: Run full test suite and lint

- [ ] **Step 1: Run all jj hook tests**

Run: `uv run --with pytest pytest jj/hooks/tests/ -v`
Expected: All tests pass.

- [ ] **Step 2: Run all worktree hook tests**

Run: `uv run --with pytest pytest .claude/hooks/tests/ -v`
Expected: All tests pass.

- [ ] **Step 3: Run lint**

Run: `lefthook run pre-commit --all-files`
Expected: No failures on modified files.

- [ ] **Step 4: Final commit if lint fixes needed**

If linting auto-fixed anything:

```text
jj commit -m "style(jj): apply lint fixes"
```
