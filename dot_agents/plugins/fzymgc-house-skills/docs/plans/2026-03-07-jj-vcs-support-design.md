# Design: jj (Jujutsu) VCS Support

**Date:** 2026-03-07
**Status:** Approved

## Goal

Add jj (Jujutsu VCS) support to fzymgc-house-skills. Skills detect whether
a repo uses jj or git and use the appropriate tool. In jj repos, agents use
jj for ALL VCS operations — only `gh` CLI remains for GitHub API calls.

## Approach: Colocated-Aware

Repos may have both `.jj/` and `.git/` (colocated). Skills detect `.jj/`
and prefer jj commands. No git commands are needed in jj repos except
through `gh` CLI for PR manipulation.

## 1. New `jj` Plugin

```text
jj/
  plugin.json
  skills/
    jujutsu/
      SKILL.md                    # Core jj workflow guidance
      references/
        jj-git-interop.md        # Colocated repo specifics, sync behavior
  commands/
    jj-init.md                   # /jj-init slash command
```

### SKILL.md

Model-invoked when `.jj/` detected or user mentions jj. Based on
[danverbraganza/jujutsu-skill](https://github.com/danverbraganza/jujutsu-skill)
(MIT), adapted for this repo's conventions.

Covers:

- Core concepts (working copy = commit, no staging, mutable history)
- Agent-safe operations (always `-m` flags, no interactive commands)
- Bookmarks, workspaces, conflict handling
- "See also: `jjagent` plugin for session-level change management"

### /jj-init Command

User-invoked slash command:

1. Check `.jj/` doesn't already exist
2. Run `jj git init --colocate` (`--colocate` required on jj >= 0.15)
3. Add `.jj/` to `.gitignore` if not already present
4. Verify with `jj st`

### Release Config

Add `jj` package to `release-please-config.json` and
`.release-please-manifest.json`.

**Implementation note (dr0.16):** Task 9 specified the package key as `"jj"` but the
actual implementation uses `"jj/skills/jujutsu"` to match the existing pattern
(`"homelab/skills/grafana"`, `"pr-review/skills/review-pr"`). Release-please uses the
key as the directory path, so the full skill path is required for correct version file
discovery.

## 2. pr-review Adaptation

### VCS Detection Preamble

Each skill (address-findings, review-pr, respond-to-comments) and each
agent (all 12) gets a detection preamble:

```markdown
## VCS Detection

Check for `.jj/` in the repo root.

- If `.jj/` exists → colocated jj repo. Use jj for ALL VCS operations.
  Consult `references/vcs-equivalence.md` for command equivalents.
- Otherwise → standard git repo. Use git commands as written below.

GitHub operations (`gh` CLI) are VCS-independent — use them regardless.
```

### New Reference File

`pr-review/references/vcs-equivalence.md` — full command mapping:

| Operation | git | jj |
|-----------|-----|-----|
| Status | `git status` / `git status --porcelain` | `jj st` |
| Diff | `git diff` | `jj diff` |
| Log | `git log --oneline` | `jj log --no-graph` |
| Show commit | `git show <ref>` | `jj show <ref>` |
| Current location | `git branch --show-current` | `jj log -r @ --no-graph -n 1` |
| File list | `git ls-files` | `jj file list` |
| Commit | `git add <files> && git commit -m "..."` | `jj commit -m "..."` |
| Push | `git push` | `jj git push --bookmark <name>` |
| Cherry-pick | `git cherry-pick <sha>` | `jj rebase -r <change-id> -d <target>` |
| Undo | `git reset` / `git revert` | `jj undo` |
| Create workspace | `git worktree add <path>` | `jj workspace add <path>` |
| Remove workspace | `git worktree remove <path>` | `jj workspace forget <name>` + rm |
| Workspace identity | `git branch --show-current` | `jj workspace root` |

### Architectural Rule: jj Commands When jj Is Available

When jj is available (`jj root` succeeds), MUST use jj commands for
ALL VCS operations — including workspace creation, commits, rebases,
and status checks. This applies to colocated repos (both `.jj/` and
`.git/`) and pure jj repos alike. Never use mutating git commands
in jj repos; read-only git commands and `gh` CLI are safe.

### Orchestrator↔Fix-Worker Changes (address-findings)

The cherry-pick workflow changes fundamentally in jj repos because
jj workspaces share the same repo — commits are immediately visible
across workspaces.

**Current git flow:**

1. Fix worker commits on `worktree/<name>` branch
2. Orchestrator finds commit: `git log --oneline <branch> -1`
3. Orchestrator cherry-picks: `git cherry-pick <sha>`
4. Orchestrator removes worktree: `git worktree remove`

**jj flow:**

1. Fix worker commits: `jj commit -m "..."`
2. Fix worker reports `CHANGE_ID` (not `WORKTREE_BRANCH`)
3. Orchestrator rebases change onto PR bookmark:
   `jj rebase -r <change-id> -d <pr-bookmark>`
4. Orchestrator updates bookmark:
   `jj bookmark set <pr-bookmark> -r <change-id>` (set creates or moves)
5. Orchestrator forgets workspace: `jj workspace forget <name>`

**Key advantages:**

- Change IDs are stable across rebases (unlike git SHAs)
- No cherry-pick conflicts from branch divergence
- No staging step (`git add`) — jj tracks all file changes automatically
- Shared repo visibility eliminates commit transfer

**Fix worker output format change:**

```text
# git repos
WORKTREE_BRANCH: worktree/fix-abc

# jj repos
CHANGE_ID: kkmpptxz
```

### Orchestrator Phase Mapping

| Phase | git | jj |
|-------|-----|-----|
| Checkout PR | `gh pr checkout <N>` | `gh pr checkout <N>` + `jj new <bookmark>` |
| Verify location | `git branch --show-current` | `jj log -r @ --no-graph` |
| Verify clean | `git status --porcelain` | `jj st` |
| Find fix commit | `git log --oneline <branch> -1` | Known via `CHANGE_ID` |
| Transfer fix | `git cherry-pick <sha>` | `jj rebase -r <change-id> -d <pr-bookmark>` |
| Conflict handling | `git cherry-pick --abort` | `jj undo` |
| Remove workspace | `git worktree remove` | `jj workspace forget` + rm directory |
| Post-batch verify | `git status --porcelain` | `jj st` |
| Push | `git push` | `jj git push --bookmark <pr-bookmark>` |
| Ship commit | `commit-commands:commit` skill | `jj commit -m "..."` |

## 3. Hook Integration — VCS-Aware Isolation

### worktree-helpers.sh

A shared helper library extracted during implementation for DRY reasons. Contains common
functions (`sanitize_for_output`, `validate_safe_name`, `detect_repo_root`) used by both
`worktree-create.sh` and `worktree-remove.sh` to avoid duplicating validation and VCS
detection logic.

### worktree-create.sh

Becomes VCS-aware:

```bash
if [[ -d "${REPO_ROOT}/.jj" ]]; then
  # jj workspace — no git worktree needed
  jj workspace add "$WORKTREE_PATH" --name "worktree-${NAME}"
else
  # Standard git worktree
  git worktree add "$WORKTREE_PATH" -b "worktree/${NAME}" HEAD
fi
```

### worktree-remove.sh

Becomes VCS-aware:

```bash
if [[ -d "${REPO_ROOT}/.jj" ]]; then
  WORKSPACE_NAME="worktree-${NAME}"
  (cd "$REPO_ROOT" && jj workspace forget "$WORKSPACE_NAME") 2>/dev/null || true
  rm -rf "$WORKTREE_PATH"
else
  git worktree remove --force "$WORKTREE_PATH" 2>/dev/null || true
fi
```

Zero git commands needed in jj repos, even for agent isolation.

**Implementation note (dr0.19):** The design showed lefthook install only in the git
branch of `worktree-create.sh`. The implementation runs `lefthook install` for both VCS
modes because colocated jj repos always have a `.git/` directory — lefthook operates on
`.git/hooks/` and works correctly in colocated repos. Skipping it in jj mode would leave
hooks uninstalled in the new workspace.

## 4. Reference Files

Three reference files (a third was extracted during implementation for DRY reasons):

| File | Purpose | Consumer |
|------|---------|----------|
| `pr-review/references/vcs-equivalence.md` | git↔jj command mapping | pr-review detection preamble |
| `jj/skills/jujutsu/references/jj-git-interop.md` | Colocated repo specifics, bookmark↔branch sync, workspace behavior | jj skill SKILL.md |
| `pr-review/references/vcs-detection-preamble.md` | Shared VCS detection shell snippet included by all agents and skills | All pr-review agents and skills (DRY extraction) |

## Out of Scope

- Changing the `homelab` plugin (no VCS dependency)
- Replacing the `jjagent` plugin (complementary, different purpose)
- Non-colocated jj repos (only colocated `.jj/` + `.git/` supported)

  **Implementation note (dr0.13):** The implementation expanded this scope as a safety
  net. `worktree-helpers.sh` adds a jj root fallback (`jj root 2>/dev/null`) so that
  `detect_repo_root` works even in non-colocated repos where `.git/` is absent. This
  does not add full non-colocated support — it only ensures the helper doesn't fail on
  such repos. All VCS operations still assume colocated layout.
- Standalone git/jj command reference docs (SKILL.md covers jj; Claude knows git)

## Testing

Use skill testing approach to validate:

- VCS detection triggers correctly (`.jj/` present vs absent)
- Command equivalence produces correct results
- Hook integration creates/removes jj workspaces properly
- Fix worker↔orchestrator handoff works with change IDs
- Colocated repo sync between jj and git stays consistent
