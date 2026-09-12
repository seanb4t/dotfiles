---
name: jujutsu
description: >-
  Jujutsu (jj) VCS workflow guidance. MUST activate on ANY VCS
  operation when `jj root` succeeds or when `.jj/` exists in the repo
  root. Use when the user mentions jj, jujutsu, or when a colocated jj
  repo is detected.
allowed-tools:
  - "Bash(jj log)"
  - "Bash(jj log *)"
  - "Bash(jj diff *)"
  - "Bash(jj st)"
  - "Bash(jj st *)"
  - "Bash(jj show *)"
  - "Bash(jj bookmark *)"
  - "Bash(jj workspace *)"
  - "Bash(jj git *)"
  - "Bash(jj new)"
  - "Bash(jj new *)"
  - "Bash(jj edit *)"
  - "Bash(jj commit *)"
  - "Bash(jj squash)"
  - "Bash(jj squash *)"
  - "Bash(jj restore)"
  - "Bash(jj restore *)"
  - "Bash(jj describe *)"
  - "Bash(jj abandon *)"
  - "Bash(jj rebase *)"
  - "Bash(jj absorb)"
  - "Bash(jj absorb *)"
  - "Bash(jj file *)"
  - "Bash(jj undo)"
  - "Bash(jj undo *)"
  - "Bash(jj redo)"
  - "Bash(jj root)"
  - "Bash(jj evolog)"
  - "Bash(jj evolog *)"
  - "Bash(jj op *)"
  - "Bash(jj util *)"
  - "Bash(jj fix)"
  - "Bash(jj fix *)"
  - "Bash(jj simplify-parents)"
  - "Bash(jj simplify-parents *)"
  - "Bash(jj config *)"
  - "Bash(jj sync)"
  - "Bash(jj tug)"
  - "Bash(jj landed)"
metadata:
  author: fzymgc-house
  version: 0.1.0 # x-release-please-version
---

# Jujutsu (jj) VCS Workflow

## Contents

- [Detection](#detection)
- [Agent Environment Rules](#agent-environment-rules)
- [Core Concepts](#core-concepts)
- [Essential Workflow](#essential-workflow)
- [Refining Commits](#refining-commits)
- [Bookmarks](#bookmarks)
- [Workspaces](#workspaces)
- [Git Integration](#git-integration)
- [GitHub Squash-Merge Workflow](#github-squash-merge-workflow)
- [Divergent Changes](#divergent-changes)
- [Conflict Handling](#conflict-handling)
- [Quick Reference](#quick-reference)
- [See Also](#see-also)

## Detection

Before any VCS operation, check for a jj repository:

```bash
if jj root >/dev/null 2>&1; then echo "jj repo detected"; fi
```

If jj is detected:

- You MUST use `jj` for all version control operations
- You MUST NOT use mutating git commands (`git commit`, `git checkout`, `git branch`,
  `git merge`, `git rebase`, etc.) -- they are blocked by a PreToolUse guard hook
- You SHOULD prefer jj equivalents over read-only git commands (`jj log` over `git log`,
  `jj diff` over `git diff`, etc.)
- You MAY use git plumbing commands (`git rev-parse`, `git ls-files`) and `gh` CLI

## Agent Environment Rules

Agents run non-interactively. These rules prevent common failures:

- You MUST run `jj git fetch` at the **start** of any task, not just before push
- You MUST use `-m` for commit/describe messages -- never open an editor
- You MUST NOT `jj describe` or rewrite commits that have already been pushed
- You MUST use **change IDs** (not commit hashes) when scripting -- they survive rewrites
- You MUST `jj commit -m "..."` before `jj new` -- `jj new` moves `@` to a new change;
  without a description or bookmark, the old change is effectively lost
- You SHOULD verify state with `jj st` after any mutation
- You SHOULD prefer `jj rebase --skip-emptied` over manual `jj abandon` -- it's idempotent and handles chains
- You MUST pass `--no-pager` on every `jj` command (e.g., `jj --no-pager log`).
  Agent environments cannot interact with pagers. Alternatively, pass
  `--config ui.paginate=never` as a flag.
- You MUST NOT redirect stderr to `/dev/null` (`2>/dev/null`) on jj commands.
  jj reports errors and important warnings on stderr. Suppressing it hides
  failures silently (e.g., `jj workspace add` appears to succeed but creates
  nothing). If jj output is noisy, use `--quiet` instead.
- If you encounter `(divergent)` markers in `jj log`, you MUST abandon the stale local copy
  and rebase remaining work onto main

**Parallel agent safety:**

- You MUST NOT dispatch multiple agents against the same jj working copy — they
  will fight over `@` and cause orphaned branches. Each parallel agent MUST work
  in its own workspace created via `jj workspace add`. The orchestrating skill
  is responsible for workspace creation before dispatch and cleanup after.
  See `references/workflows-reference.md` "Agent Fan-Out" for the full pattern.

**You MUST NOT use these interactive commands (they hang in agent environments):**

| Command | Why | Alternative |
|---------|-----|-------------|
| `jj split` | Opens editor to select hunks | Manually edit files, commit separately |
| `jj resolve` | Opens merge tool | Edit conflict markers directly |
| `jj squash -i` | Interactive hunk selection | Use `jj squash` (non-interactive) |

## Core Concepts

### Working Copy Is a Commit

In jj, the working copy is always a commit (`@`). There is no staging area. Every file change
is automatically part of the working-copy commit.

### Change IDs vs Commit IDs

| Property | Change ID | Commit ID |
|----------|-----------|-----------|
| Format | Short alpha string (e.g., `kxryzmsp`) | SHA hex (e.g., `a1b2c3d4`) |
| Stability | Stable across rewrites | Changes on rewrite |
| Use for | Referring to logical changes | Pinpointing exact versions |

You MUST prefer change IDs when referring to revisions -- they survive `squash`, `rebase`, and `amend`.

### Key Revsets

| Symbol | Meaning |
|--------|---------|
| `@` | Working copy (current change) |
| `@-` | Parent of working copy |
| `@--` | Grandparent of working copy |
| `root()` | Root commit |
| `trunk()` | Main branch tracking commit |

## Essential Workflow

### Create and Describe Commits

```bash
# Describe current change and start a new empty one (like git commit)
jj commit -m "feat(scope): add new feature"

# Create a new empty change on top of current
jj new

# Update description of current change without creating a new one
jj describe -m "fix(scope): correct the bug"
```

### View History and Changes

```bash
# View commit log (default: mutable revisions with context)
jj log

# View log with all revisions
jj log -r '::'  # all() also works but :: is canonical

# Show diff of current working copy
jj diff

# Show diff of a specific revision
jj show <rev>

# Status of working copy
jj st
```

## Refining Commits

### Squash Changes

```bash
# Move all changes from @ into @- (squash into parent)
jj squash

# Move changes from @ into a specific revision
jj squash --into <rev>
```

### Absorb Changes

```bash
# Auto-distribute working copy changes to the commits that last modified those lines
jj absorb

# Absorb only specific files
jj absorb src/auth/ tests/

# Review what absorb did
jj op show -p
```

This automatically routes each hunk to the right ancestor commit using blame data.
Ambiguous hunks (spanning multiple ancestors) stay in the source. Source is abandoned
if it becomes empty and has no description.

### Evolution Log (Recovery)

```bash
# Trace all versions of a change (including auto-snapshots)
jj evolog --patch
```

Use `jj evolog` to find a lost intermediate state, then `jj new <commit-id>` to recover.

### Abandon, Undo, and Restore

```bash
# Remove a commit (descendants rebased onto its parent; changes are discarded)
jj abandon <rev>

# Undo the last jj operation
jj undo

# Discard all changes in the working copy
jj restore

# Restore a specific file from a revision
jj restore --from <rev> <path>
```

**Warning — op log semantics:** The op log only records **successful** operations.
A failed jj command leaves no trace in the op log (unlike git's reflog). `jj undo`
always targets the most recent *successful* operation — do NOT "undo twice" to
account for a failure. If you need to recover from a bad state, use
`jj op log` to find the right operation ID, then `jj op restore <op-id>`.
See `references/jj-reference.md` for the full op log reference.

**Note:** You MUST NOT use `jj split` -- it is interactive and hangs in agent environments. To split a commit
(extract specific files into a new child):

1. `jj new <commit>` — create a new empty change after the target
2. `jj squash --from <commit> <path1> <path2>` — move only those files from the target into the new change

The target commit retains everything except the moved files.

## Bookmarks

Bookmarks are jj's equivalent of git branches.

```bash
# Create a bookmark at the current change
jj bookmark create <name>

# Move a bookmark to a specific revision (creates if missing)
jj bookmark set <name> -r <rev>

# List all bookmarks
jj bookmark list

# Delete a bookmark
jj bookmark delete <name>
```

Short forms: `jj b c`, `jj b s`, `jj b l`, `jj b d`.

Bookmarks do NOT auto-advance when you create new commits. You MUST explicitly
update them before pushing:

```bash
jj bookmark set my-feature -r @
jj git push -b my-feature
```

## Workspaces

Workspaces provide isolated working copies sharing the same repo storage. You SHOULD
create a workspace for each feature or task — they are near-instant and cost almost
no disk space. See `references/workflows-reference.md` "Workspace-Per-Feature Workflow"
for the full end-to-end pattern including push-from-primary and cleanup.

You MUST use `jj workspace add` — you MUST NOT use `git worktree add`. This applies
to both colocated and pure jj repos.

```bash
# Create a workspace
jj workspace add ../my-workspace --name my-workspace

# List workspaces
jj workspace list

# Forget a workspace (de-register, does NOT delete files — callers must rm -rf the directory after)
jj workspace forget <name>
rm -rf <path>

# Fix a stale workspace after concurrent edits
jj workspace update-stale
```

Key behaviors:

- `jj workspace list` shows all workspaces (format: `<name>: <change-id-prefix> <commit-id-prefix> <description>`,
  e.g. `default: rwoumssn 094ee48c (empty) (no description set)`); there is no
  `(current)` marker — identify the current workspace from the working directory
  path (sibling worktrees use `<repo>_worktrees/<workspace-name>/`)
- Each workspace has its own working-copy commit (`@`)
- Changes committed in one workspace are immediately visible in others
- Use `jj workspace update-stale` if a workspace falls behind

## Git Integration

For full details, read `references/jj-git-interop.md`.

### Push and Fetch

```bash
# Push a bookmark to its remote
jj git push -b <bookmark>

# Push the current change (auto-generates a bookmark named push-<id>)
jj git push --change @

# Fetch from all remotes
jj git fetch
```

### Colocated Repos

In colocated repos (both `.jj/` and `.git/` present), every `jj` command auto-syncs
with the underlying git repo. The `gh` CLI works normally because it reads `.git/`.

### Creating a PR

```bash
# Ensure bookmark exists and is at the right revision
jj bookmark set my-feature -r @
jj git push -b my-feature

# Create PR via GitHub CLI
gh pr create --head my-feature --title "..." --body "..."
```

## GitHub Squash-Merge Workflow

GitHub squash-merge creates a **new commit** on `main` with a different hash than your local
commits. jj cannot detect that your work has "landed," causing local commits to appear
alive/divergent after fetch.

### Post Squash-Merge Reconciliation

After a PR is squash-merged on GitHub:

```bash
jj git fetch
jj rebase -o main --skip-emptied
jj bookmark delete <merged-bookmark>
```

`--skip-emptied` is critical -- it automatically abandons commits that become empty after
rebase (their content is already in `main` via the squash merge).

### Stacked PRs

If you had commits A -> B -> C -> D (each a separate PR) and A's PR was just squash-merged:

```bash
jj git fetch
jj rebase -s <change-id-of-B> -o main --skip-emptied
jj bookmark delete <a-bookmark>
```

A becomes empty and is auto-abandoned. B, C, D rebase cleanly onto new `main`.

### Complete PR Lifecycle

```bash
# 1. Start work
jj new main
# ... make changes ...
jj describe -m "feat: my feature"
jj bookmark create my-feature -r @
jj git push

# 2. Address review comments
jj new my-feature   # new child of bookmark tip
# ... make fixes ...
jj squash           # fold fixes into parent
jj git push --bookmark my-feature

# 3. After squash-merge on GitHub
jj git fetch
jj rebase -o main --skip-emptied
jj bookmark delete my-feature

# 4. Start next piece of work
jj new main
```

For detailed workflows and aliases, see `references/workflows-reference.md`.

## Divergent Changes

Divergent changes appear as `(divergent)` in `jj log` when a commit is modified both locally and remotely.

### How Divergence Happens

1. Push a bookmark for PR
2. Locally `jj describe` or `jj squash` to tweak the commit
3. PR gets squash-merged on GitHub (remote bookmark moves)
4. `jj git fetch` -> two commits with the same change ID = divergence

### Prevention Rules

- You MUST NOT modify commits after pushing -- if the PR is up for review, leave those commits alone
- You MUST run `jj git fetch` before starting new work
- You MUST use change IDs, not commit hashes -- change IDs survive rewrites

### Resolving Divergence

If divergence occurs, abandon the stale local copy:

```bash
jj abandon <stale-commit-hash>
```

Or use the idempotent approach -- rebase with `--skip-emptied` to clean up automatically.

## Conflict Handling

jj records conflicts inside commits rather than blocking operations: rebases,
merges, and `jj new` always succeed, and descendants of a conflicted commit
inherit a tagged conflict that auto-clears when the ancestor is fixed.

### Detecting Conflicts

```bash
jj st                       # Per-file status with "Conflict" markers
jj log -r 'conflicts()'     # All commits with unresolved conflicts
jj resolve --list           # Conflicted paths in @ (does not launch a merge tool)
```

### Canonical Resolution Workflow

The official jj tutorial -- and jj's own auto-printed hint after a rebase
produces conflicts -- gives this exact recipe. Follow it:

```bash
jj new <lowest-conflicted-commit>   # 1. Resolution commit on top of it
$EDITOR <conflicted-file>           # 2. Edit markers (or jj resolve; see below)
jj diff                             # 3. Verify ONLY the resolution shows
jj squash                           # 4. Fold into the conflicted ancestor
```

**Always resolve at the lowest conflicted ancestor**, never the tip. `jj squash`
auto-rebases descendants and reports `Existing conflicts were resolved or
abandoned from N commits` -- a single resolution heals the entire stack.

**Why `jj new` + `jj squash` instead of `jj edit`:** the resolution lives in
its own change ID, so `jj diff` shows only the fix, `jj abandon @` cleanly
reverts a misstep, and `jj op log` records two reversible operations instead
of one hard-to-undo mutation.

### Editing Markers vs `jj resolve`

`jj resolve` invokes an external 3-way merge tool one file at a time. It only
supports 2-sided conflicts and requires a TTY.

| Context | Approach |
|---------|----------|
| Interactive human | Set `ui.merge-editor = "mergiraf"` (structural, language-aware) and use `jj resolve`. Built-in alternatives: `meld`, `kdiff3`, `vscode`, `vimdiff`, `smerge`. |
| Non-interactive agent | **MUST NOT use `jj resolve`** -- it hangs without a TTY. Edit conflict markers directly in the file. `references/jj-agent-config.md` neutralizes the merge editor with `merge-editor = ":"` as a safety net. |
| Pick one whole side | `jj resolve --tool :ours` or `--tool :theirs` (built-in pseudo-tools) |
| 3+ sided conflicts | Marker editing only -- `jj resolve` cannot handle these |

For the snapshot+diff marker format and how to read it line by line, see
`references/jj-reference.md` "Conflict Markers".

### Stack Rebase Example

```bash
jj rebase -s B2 -o A                 # → conflicts in B2 and C; rebase completes
jj log -r 'conflicts()'              # → B2, C
jj new B2                            # resolution commit on lowest ancestor
$EDITOR file1                        # apply each %%%%%%% diff to the +++++++ snapshot
jj diff                              # verify only the resolution shows
jj squash                            # → "conflicts resolved from 2 commits"
jj log -r 'conflicts()'              # → empty
```

C automatically inherits the resolution -- never resolve the same conflict twice.

## Quick Reference

| Task | Command |
|------|---------|
| Commit and start new change | `jj commit -m "msg"` |
| Describe current change | `jj describe -m "msg"` |
| New empty change | `jj new` |
| New change on specific parent | `jj new <rev>` |
| New merge change | `jj new <rev1> <rev2>` |
| Insert change mid-chain | `jj new -A <after> -B <before>` |
| View log | `jj log` |
| View diff | `jj diff` |
| Show revision | `jj show <rev>` |
| Status | `jj st` |
| Squash into parent | `jj squash` |
| Squash into specific rev | `jj squash --into <rev>` |
| Absorb into ancestors | `jj absorb` |
| Trace change history | `jj evolog --patch` |
| Abandon change | `jj abandon <rev>` |
| Undo last operation | `jj undo` |
| Redo after undo | `jj redo` |
| Revert specific past op | `jj op revert <op-id>` |
| Restore working copy | `jj restore` |
| Rebase onto new parent | `jj rebase -s <src> -o <dest>` |
| Rebase single rev (extract) | `jj rebase -r <rev> -o <dest>` |
| Insert rev after target | `jj rebase -r <rev> -A <target>` |
| Rebase all branches | `jj rebase -s 'all:roots(trunk()..@)' -o trunk()` |
| Create bookmark | `jj bookmark create <name>` |
| Move bookmark | `jj bookmark set <name> -r <rev>` |
| Advance bookmark to @ | `jj bookmark advance <name>` |
| Push bookmark | `jj git push -b <name>` |
| Push with auto-bookmark | `jj git push --change @` |
| Push all tracked | `jj git push --tracked` |
| Fetch remotes | `jj git fetch` |
| List files | `jj file list` |
| Current location | `jj log -r @ --no-graph -T 'change_id.short(8)'` |
| Manual snapshot | `jj util snapshot` |
| Add workspace | `jj workspace add <path> --name <name>` |
| List workspaces | `jj workspace list` |
| Remove workspace | `jj workspace forget <name>` + `rm -rf <path>` |

## See Also

- `references/jj-reference.md` -- detailed jj command reference, revsets, absorb, evolog, and advanced operations
- `references/workflows-reference.md` -- end-to-end workflow recipes, aliases, stacked PR patterns, agent fan-out, megamerge
- `references/jj-git-interop.md` -- colocated repo behavior, auto-sync sequence, conflict storage, and git compatibility
- `references/jj-agent-config.md` -- recommended jj configuration for non-interactive agent environments
