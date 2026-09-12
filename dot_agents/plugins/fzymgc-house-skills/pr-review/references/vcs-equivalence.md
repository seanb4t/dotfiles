# VCS Command Equivalence: git and jj

Use this reference when the repo has `.jj/` (colocated or pure jj repo).

**Rule:** When jj is available (`jj root` succeeds), MUST use jj commands
for ALL VCS operations — including workspace creation, commits, rebases,
and status checks. Never use mutating git commands (`git commit`,
`git worktree add`, `git checkout`, etc.) in jj repos. Read-only git
commands and `gh` CLI are safe.

**Note:** The detection pattern (see `vcs-detection-preamble.md`) uses `jj root`
first, then `git rev-parse --git-dir`, and reports "none" if neither succeeds.
This command-based approach works in workspaces where `.jj/` or `.git` may not
exist as directories (e.g., jj workspaces, git worktrees). Agents verify VCS
availability in their Environment startup check (step 2) — if verification fails,
they STOP and report STATUS: FAILED.

## Command Mapping

| Operation | git | jj |
|---|---|---|
| Status | `git status --porcelain` | `jj st` |
| Diff (working copy) | `git diff` | `jj diff` |
| Diff (specific rev) | `git diff <ref>` | `jj diff -r <ref>` |
| Diff (range) | `git diff A..B` | `jj diff --from A --to B` |
| Log | `git log --oneline` | `jj log --no-graph` |
| Log (with patch) | `git log -p` | `jj log -p` |
| Show commit | `git show <ref>` | `jj show <ref>` |
| File list | `git ls-files` | `jj file list` |
| Stage + commit | `git add <files> && git commit -m "..."` | `jj commit -m "..."` |
| Push | `git push` | `jj git push -b <name>` |
| Push (auto-bookmark) | *(no equivalent)* | `jj git push --change <id>` |
| Fetch | `git fetch` | `jj git fetch` |
| Cherry-pick | `git cherry-pick <sha>` | `jj rebase -r <change-id> -o <target>` |
| Undo | `git reset` / `git revert` | `jj undo` |
| Create workspace | `git worktree add <path> -b <branch> HEAD` | `jj workspace add <path> --name <name>` |
| Remove workspace | `git worktree remove <path>` | `jj workspace forget <name>` + `rm -rf <path>` |
| List workspaces | `git worktree list` | `jj workspace list` |
| Current location | `git branch --show-current` | `jj log -r @ --no-graph -T 'change_id.short(8)'` |

## Key Differences

- **No staging area:** jj tracks all file changes automatically. No `git add`.
- **Change IDs:** Use change IDs (stable across rebases) instead of commit SHAs.
- **Mutable commits:** All commits can be freely modified, split, squashed.
- **Working copy = commit:** The working directory is always a commit (`@`).
- **Bookmarks don't auto-advance:** Must `jj bookmark set` before pushing.

## Agent Output Fields

### Fix-Worker Output Contract

Fix-worker agents MUST report these fields:

| Field | Required | Description |
|-------|----------|-------------|
| STATUS | Always | FIXED, PARTIAL, or FAILED |
| FINDING | Always | Bead ID of the finding being addressed |
| VCS | Always | "git" or "jj" |
| FILES_CHANGED | When FIXED | Comma-separated list of changed files |
| DESCRIPTION | When FIXED | One-line summary of the fix |
| WORKTREE_BRANCH | When VCS=git | Branch name (e.g., worktree/agent-xxx) |
| CHANGE_ID | When VCS=jj | jj change ID (e.g., abc12345) |

**Discriminated union rule:** When VCS=git, include WORKTREE_BRANCH and
omit CHANGE_ID. When VCS=jj, include CHANGE_ID and omit
WORKTREE_BRANCH. "Omit" means do not include the line at all (not an
empty value).

```text
git repos: WORKTREE_BRANCH: worktree/fix-abc
jj repos:  CHANGE_ID: kkmpptxz
```

## Operations That Stay git/gh

- `gh pr create/view/diff/checkout` -- GitHub CLI (VCS-independent)
- `gh api` -- GitHub API calls
- `gh pr comment` -- PR comments
