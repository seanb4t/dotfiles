# jj Command Reference

Detailed command reference for Jujutsu (jj) operations beyond the essentials in SKILL.md.

## Revset Expressions

Revsets are jj's query language for selecting revisions.

### Common Revsets

| Expression | Meaning |
|------------|---------|
| `@` | Working copy commit |
| `@-` | Parent of working copy |
| `@--` | Grandparent |
| `trunk()` | Main branch tip |
| `root()` | Repository root |
| `all()` or `::` | All revisions |
| `visible_heads()` | All head revisions |
| `bookmarks()` | All bookmarked revisions |
| `remote_bookmarks()` | All remote-tracking bookmarks |
| `mine()` | Revisions authored by you |
| `empty()` | Empty revisions (no diff) |
| `conflicts()` | Revisions with unresolved conflicts |
| `description(pattern)` | Revisions matching description |
| `author(pattern)` | Revisions by author |

### Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `x & y` | Intersection | `mine() & bookmarks()` |
| `x \| y` | Union | `@- \| @--` |
| `~x` | Complement (not) | `~empty()` |
| `x-` | Parents | `@-` (parent of @) |
| `x+` | Children | `trunk()+` (children of trunk) |
| `x..y` | Range (ancestors of y, not ancestors of x) | `trunk()..@` |
| `::x` | Ancestors of x (inclusive) | `::@` |
| `x::` | Descendants of x (inclusive) | `trunk()::` |

### Useful Queries

```bash
# All your unpushed work
jj log -r 'mine() & ~ancestors(trunk())'

# Commits on current branch not yet on main
jj log -r 'trunk()..@'

# All bookmarked commits that are empty
jj log -r 'bookmarks() & empty()'

# Commits with conflicts
jj log -r 'conflicts()'

# All mutable (non-immutable) commits
jj log -r 'mutable()'
```

## Conflict Markers

For the canonical resolution workflow (`jj new` → edit → `jj diff` → `jj squash`)
see SKILL.md "Conflict Handling". This section documents the marker format itself.

### Snapshot+Diff Format (jj 0.39+, default)

`ui.conflict-marker-style = "diff"` materializes conflicts as one full snapshot
plus one diff per other side. Resolve by applying each diff to the snapshot.

```text
<<<<<<< conflict 1 of 1
%%%%%%% diff from: vpxusssl 38d49363 "merge base"
\\\\\\\        to: rtsqusxu 2768b0b9 "commit A"
 apple
-grape
+grapefruit
 orange
+++++++ ysrnknol 7a20f389 "commit B"
APPLE
GRAPE
ORANGE
>>>>>>> conflict 1 of 1 ends
```

| Marker | Meaning |
|--------|---------|
| `<<<<<<< conflict N of M` | Block start (numbered when a file has multiple conflicts) |
| `+++++++ <commit>` | Snapshot of one side -- full content |
| `%%%%%%% diff from: ... to: ...` | Diff to apply to the snapshot to reach another side |
| `\\\\\\\` | Header continuation for the long `diff from`/`to` label |
| `>>>>>>> conflict N of M ends` | Block end |

To resolve: pick the snapshot side (`+++++++` block), mentally (or in `$EDITOR`)
apply each `%%%%%%%` diff to it, write the final content into the file, delete
all marker lines (`<<<`, `+++`, `%%%`, `\\\`, `>>>`), save. Then `jj st` should
report no conflict on that file. Resolution example for the snippet above:

```text
APPLE
GRAPEFRUIT
ORANGE
```

### Multi-Sided Conflicts

When 3+ commits are merged at once, jj produces a single `+++++++` snapshot and
multiple `%%%%%%%` diff blocks. Apply each diff in turn. **`jj resolve` cannot
handle 3+ sided conflicts** -- marker editing is the only path.

### Alternative Marker Styles

```toml
[ui]
conflict-marker-style = "snapshot"  # Show full content of every side, no diffs
conflict-marker-style = "git"       # diff3 format; falls back to "snapshot" for 3+ sides
```

The `"git"` style produces standard `<<<<<<<`/`|||||||`/`=======`/`>>>>>>>`
markers compatible with tools that expect git's diff3 output, but only for
2-sided conflicts.

### Long Markers

If a file's contents could be confused for conflict markers (e.g. lines
starting with `=======`), jj extends marker length, e.g. `<<<<<<<<<<<<<<<` and
`%%%%%%%%%%%%%%%`. Match the actual length when removing them.

## Templates

Templates control output formatting in `jj log`, `jj show`, etc.

```bash
# Show only change IDs (useful for scripting)
jj log -r @ --no-graph -T 'change_id.short(8)'

# Show change ID and commit ID together
jj log -T 'change_id.short(8) ++ " " ++ commit_id.short(8) ++ " " ++ description.first_line()'

# Get the full change ID of current revision
jj log -r @ --no-graph -T 'change_id'
```

## Advanced Rebase

### Source Modes

| Flag | Behavior |
|------|----------|
| `-r <rev>` | Moves ONLY the specified revision; children reparented onto its parent. **Unique:** can rebase onto own descendant. |
| `-s <rev>` | Moves the revision and all its descendants (subtree) |
| `-b <rev>` | Moves the entire branch (equivalent to `-s 'roots(dest..rev)'`) |
| (none) | Defaults to `-b @` |

### Destination Modes

| Flag | Behavior |
|------|----------|
| `-o <dest>` | Rebase onto dest; existing descendants of dest unaffected |
| `-A <dest>` | Insert after dest: reparent dest's children onto the rebased revisions |
| `-B <dest>` | Insert before dest: rebase onto dest's parents, reparent dest onto rebased revisions |

`-A` and `-B` can be combined. Multiple destinations create merge commits.

### Key Flags

| Flag | Behavior |
|------|----------|
| `--skip-emptied` | Auto-abandons commits that become empty after rebase (NOT those already empty). Never skips merge commits with multiple non-empty parents. |
| `--keep-divergent` | Keeps divergent copies during rebase instead of auto-abandoning them |
| `--simplify-parents` | Removes redundant parents (ancestors of other parents) during rebase |

### Rebase Recipes

```bash
# Rebase a single revision (detach from its current location)
jj rebase -r <rev> -o <dest>

# Rebase a subtree (revision and all descendants)
jj rebase -s <rev> -o <dest>

# Rebase a range (branch of revisions)
jj rebase -b <rev> -o <dest>

# Rebase with auto-abandon of emptied commits
jj rebase -o <dest> --skip-emptied

# Reorder: move M to right after J (before K)
jj rebase -r M -A J
# Result: J → M' → K' → L'

# Insert X between B and C
jj rebase -r X -A B
# B's children (including C) become children of X

# Insert before: move K before L
jj rebase -r K -B L
# K becomes L's parent; L and descendants shift up

# Create a merge commit via multi-destination rebase
jj rebase -s L -o K -o M

# Rebase all branches onto updated main at once
jj rebase -s 'all:roots(trunk()..@)' -o trunk() --skip-emptied
# The all: prefix is required when revset returns multiple revisions
```

## Absorb

Automatically distributes working-copy changes to the ancestor commits that last
modified those lines. Replaces the `git add -p → git commit --fixup → git rebase -i --autosquash`
workflow with a single command.

```bash
# Absorb all working copy changes into mutable ancestors
jj absorb

# Absorb only specific files/paths
jj absorb src/auth/ tests/

# Absorb from a specific revision (not just @)
jj absorb --from <rev>

# Limit how far back it looks
jj absorb --into 'ancestors(@, 5)'

# Review what absorb did
jj op show -p
```

**Algorithm:** For each changed hunk, jj uses file annotation (like `git blame`) to find
which ancestor last modified those lines. If the hunk maps unambiguously to one ancestor,
it's moved there. Ambiguous hunks stay in the source. The source is abandoned if it becomes
empty and has no description.

## Evolution Log (evolog)

Traces the complete history of a single ChangeId across all rewrites, including
auto-snapshots. Critical for understanding what happened to a change and recovering work.

```bash
# Show all versions of the current change
jj evolog

# Show with file-level patches (see every intermediate state)
jj evolog --patch

# Show evolog for a specific change
jj evolog -r <change-id>
```

## Bookmark Management

### Tracking and Untracking

```bash
# Start tracking a remote bookmark (auto-merge on fetch)
jj bookmark track <name>@<remote>

# Stop tracking
jj bookmark untrack <name>@<remote>

# List with tracking info
jj bookmark list --all
```

### Bookmark Patterns

```bash
# Move bookmark to current working copy
jj bookmark set <name> -r @

# Move bookmark to parent (useful after jj new)
jj bookmark set <name> -r @-

# Auto-advance closest bookmark to @ (solves the "forgot to move bookmark" footgun)
jj bookmark advance <name>

# Force-push after bookmark move
jj git push -b <name>

# Forget a bookmark (local only, does NOT propagate deletion to remote)
jj bookmark forget <name>

# Delete a bookmark (propagates deletion to remote on next push)
jj bookmark delete <name>
```

## File Operations

```bash
# List all tracked files
jj file list

# List files in a specific revision
jj file list -r <rev>

# Show file at a specific revision (like git show <rev>:<file>)
jj file show -r <rev> <path>

# Show changes to a specific file
jj diff <path>
jj diff -r <rev> <path>
```

## Operation Log

jj tracks all operations for undo/redo. The op log is **global** (shared across
all workspaces) and **lock-free** (concurrent operations create a DAG that is
auto-merged).

```bash
# View operation history
jj op log

# Show what changed in the last operation (with patches)
jj op show -p

# Compare repo state between two operations
jj op diff --from <op1> --to <op2> -s

# Undo last operation (repeatable -- walks further back each time)
jj undo

# Redo after undo (walks forward)
jj redo

# Restore to a specific operation (bulk reset)
jj op restore <op-id>

# Surgically invert ONE past operation (keeps later work)
jj op revert <op-id>

# Selectively revert (experimental): repo state only, keep remote-tracking
jj op revert <op-id> --what=repo

# View repo as it was at a past operation (read-only inspection)
jj --at-op=<op-id> log

# Prune old operation history
jj op abandon ..<op-id>
jj util gc                  # garbage collect unreachable objects
jj util gc --expire=now     # immediate cleanup (careful!)
```

### When to Use Which

| Command | Use Case |
|---------|----------|
| `jj undo` | Quick "oops" for the last command |
| `jj op restore <id>` | Reset to a known good state (bulk undo) |
| `jj op revert <id>` | Undo one past operation, keep everything after it |

**Important:** The op log only records **successful** operations. A failed command
leaves no op-log entry. `jj undo` always targets the most recent successful
operation — you MUST NOT "undo twice" to account for a failure.

## Push Safety

`jj git push` uses **force-with-lease semantics** automatically. The remote is
updated only if its current state matches what jj last fetched. No `--force`
flag is needed or available.

```bash
# Push specific bookmarks
jj git push -b <name>

# Push with auto-generated bookmark (creates push-<change-id-prefix>)
jj git push --change @

# Push with explicit name in one shot
jj git push --named my-feature=@

# Push all tracked bookmarks
jj git push --tracked

# Preview without pushing
jj git push --dry-run

# Allow pushing commits with empty descriptions
jj git push --allow-empty-description
```

## Snapshot Control

jj snapshots the working copy at the start of every command. Control this with:

```bash
# Manual snapshot trigger (useful for scripting/cron)
jj util snapshot
jj util snapshot --quiet

# Skip snapshot (shows potentially stale state; useful for prompts)
jj log --ignore-working-copy

# Config: max file size for auto-tracking new files (default 1 MiB)
# In config.toml: snapshot.max-new-file-size = "10MiB"
```

## Fix (Auto-Format Across History)

Runs configured formatters on files in mutable commits and all their descendants.
Unlike `jj absorb` (which routes working-copy changes to ancestors by blame),
`jj fix` pipes file content through external tools and rewrites commits in place.

```bash
# Fix all changed files in your mutable stack (default revset)
jj fix

# Fix specific files only
jj fix src/main.py tests/

# Fix starting from a specific commit (and all descendants)
jj fix -s <rev>

# Fix ALL files (not just changed ones)
jj fix --include-unchanged-files
```

**Configuration** (in config.toml):

```toml
[fix.tools.ruff-format]
command = ["ruff", "format", "--stdin-filename=$path", "-"]
patterns = ["glob:'**/*.py'"]

[fix.tools.prettier]
command = ["prettier", "--stdin-filepath=$path"]
patterns = ["glob:'**/*.{js,ts,jsx,tsx,json,css}'"]
```

**Key properties:**

- Deterministic: same input always produces same output (required for dedup)
- Deduplicates: identical file content at the same path runs through the tool only once
- Never creates new conflicts
- Files with existing conflicts are fixed on all sides of the conflict
- Descendants are auto-fixed too, so formatting fixes propagate down the stack

## Additional Revsets

```bash
# All your unpushed work
jj log -r 'mine() & ~ancestors(trunk())'

# Stack of commits you're working on
jj log -r 'reachable(@, mutable())'

# Commits with conflicts
jj log -r 'conflicts()'

# Divergent commits (same change ID, different content)
jj log -r 'divergent()'

# Safe scripting: evaluates to none() if rev doesn't exist
jj log -r 'present(my-bookmark)'

# Newest N commits by timestamp
jj log -r 'latest(mine(), 5)'

# Fork point of commits
jj log -r 'fork_point(@)'

# All immutable commits (trunk + tags + untracked remotes)
jj log -r 'immutable()'

# All mutable commits
jj log -r 'mutable()'
```

## Diff Formats

```bash
# Default diff
jj diff

# Git-style diff
jj diff --git

# Summary only (files changed)
jj diff --summary

# Stat (insertions/deletions per file)
jj diff --stat

# Diff between two revisions
jj diff --from <rev1> --to <rev2>
```
