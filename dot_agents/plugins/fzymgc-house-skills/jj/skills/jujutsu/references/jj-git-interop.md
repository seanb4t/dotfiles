# jj-git Interop Reference

How jj and git coexist in colocated repositories.

## Colocated Repo Behavior

A colocated repo has both `.jj/` and `.git/` directories. Most `jj` commands automatically sync
state to the underlying git repo. This means git-based tools (GitHub CLI, IDE git integration) see
an up-to-date `.git/` at all times.

## Bookmark-Branch Sync

jj **bookmarks** map directly to git **branches**:

- On most `jj` commands, git branches are auto-imported as jj bookmarks
- On most `jj` commands, jj bookmark changes are auto-exported as git branches
- `jj bookmark list` shows all bookmarks (equivalent to `git branch -a` after import)
- `jj bookmark create <name>` creates a bookmark at the current change (`@`)
- `jj bookmark set <name> -r <rev>` creates or moves a bookmark to the specified revision

## Push and Fetch

```bash
jj git push -b <bookmark>      # Push a specific bookmark to its remote
jj git push --change <rev>     # Auto-create bookmark and push (e.g., push-kxryzmsp)
jj git push --all               # Push all bookmarks
jj git fetch                    # Fetch from all remotes
jj git fetch --remote origin    # Fetch from a specific remote
```

`jj git push --change <rev>` automatically creates a bookmark named `push-<change-id-prefix>` (e.g.,
`push-kxryzmsp`). The exact prefix length may vary by jj version. Use `jj bookmark list` after pushing
to see the auto-created bookmark name.

After fetching, new remote branches appear as `<bookmark>@<remote>` (e.g., `main@origin`).

## Detached HEAD

jj puts git into **detached HEAD** state. This is normal and expected. You MUST NOT attempt to
"fix" it by checking out a branch in git. jj manages the git HEAD internally to track the
current working copy commit.

## GitHub CLI Compatibility

`gh` works in colocated repos because it only needs `.git/`:

```bash
gh pr list                      # Works normally
gh pr create --head <bookmark>  # Use the jj bookmark name as the branch
gh pr view 123                  # Works normally
```

Ensure the bookmark is pushed (`jj git push -b <name>`) before creating a PR.

## Workspaces

Workspaces replace git worktrees in jj repos. You MUST use `jj workspace add` —
you MUST NOT use `git worktree add`. This applies to both colocated and pure jj repos. See the [Workspaces section in
SKILL.md](../SKILL.md#workspaces) for full command reference and key behaviors.

Key removal note: `jj workspace forget` de-registers a workspace but does NOT delete
files — callers must `rm -rf` the workspace directory after forget.

## Auto-Sync Sequence (Every jj Command)

In colocated repos, every jj command runs this sequence:

1. **Import Git HEAD** — detect external `git checkout` etc.
2. **Snapshot working copy** — auto-commit filesystem changes into `@`
3. **Import Git refs** — update jj bookmarks from `refs/heads/*`
4. **Execute the command** — the actual jj operation
5. **Export Git refs** — write jj bookmark changes back to `refs/heads/*`
6. **Update Git HEAD** — set `.git/HEAD` to working-copy parent (detached)
7. **Update working copy** — write files to disk to match new `@`

Manual import/export (`jj git import`/`jj git export`) is unnecessary in
colocated repos — it happens automatically.

## GC Protection

jj creates refs in `refs/jj/keep/*` to prevent Git's garbage collector from
removing commits that jj still references but have no Git branch. Run
`jj util gc` to clean up unreachable refs after abandoning work.

## Conflict Storage in Git

Commits with jj-internal conflicts are stored as Git commits with special tree
entries (`.jjconflict-base-*/` and `.jjconflict-side-*/` directories). The
authoritative conflict data is in a non-standard `jj:trees` commit header.
You MUST NOT `git checkout` a conflicted commit — use `jj` to navigate to it.

## Change ID Header

jj stores Change IDs in a non-standard Git commit header. This header is
preserved by most forges (GitHub, GitLab) and controlled by the
`git.write-change-id-header` config flag. Losing it doesn't break anything
but means the change ID is regenerated.

## What NOT To Do

You **MUST NOT** use mutating git commands when jj is available (colocated or pure):

| Avoid | Use Instead |
|-------|-------------|
| `git commit` | `jj commit` or `jj describe` + `jj new` |
| `git merge` | `jj new branch1 branch2` (creates merge commit) |
| `git rebase` | `jj rebase -s <source> -o <dest>` |
| `git checkout <branch>` | `jj edit <bookmark>` (edit tip) or `jj new <bookmark>` (new child) |
| `git branch -d` | `jj bookmark delete <name>` |
| `git worktree add` | `jj workspace add` |

**Read-only git commands are fine**: `git log`, `git diff`, `git status`, `git rev-parse`, `git remote -v`.

If a mutating git command causes sync issues, use `jj undo` to revert to the previous jj state.

## Recovery from Accidental `git commit`

If someone runs `git commit` in a colocated repo:

1. Git creates a commit on detached HEAD
2. Next `jj` command auto-imports it (appears in `jj op log` as "import git refs")
3. Recovery: `jj undo` reverts the import, or simply use `jj abandon` on the unwanted commit

## Known Limitations

| Area | Status |
|------|--------|
| Git hooks | Not supported (issue #405). Use `jj-pre-push` package or `jj util exec` aliases. |
| Git submodules | Not supported. Use native `git submodule` in colocated mode. |
| Git LFS | Not supported (issue #80) |
| Secondary workspace `.git/` | Missing — tools requiring `.git/` won't work (PR #4644) |
| Git staging area/index | Ignored by jj. Use `jj split`/`jj squash` instead. |
