# VCS Preamble

Detect the active VCS and use the appropriate commands throughout the skill.

## Detection

```bash
if jj root >/dev/null 2>&1; then
  VCS=jj
else
  VCS=git
fi
```

## Command Mapping

| Operation | git | jj |
|-----------|-----|-----|
| Create workspace | `git worktree add ../<repo>_worktrees/<name> -b <branch>` | `jj workspace add ../<repo>_worktrees/<name> --name <name>` |
| List workspaces | `git worktree list` | `jj workspace list` |
| Remove workspace | `git worktree remove <path>` | `jj workspace forget <name>` + `rm -rf <path>` |
| Commit | `git add <files> && git commit -m "msg"` | `jj commit -m "msg"` |
| Describe/amend | `git commit --amend -m "msg"` | `jj describe -m "msg"` |
| New change | N/A (implicit with commit) | `jj new` |
| Create branch/bookmark | `git checkout -b <name>` | `jj bookmark create <name> -r @` |
| Push | `git push -u origin <branch>` | `jj bookmark set <name> -r @ && jj git push -b <name>` |
| Fetch | `git fetch` / `git pull` | `jj git fetch` |
| Diff range (review) | `git diff <base_sha>..<head_sha>` | `jj diff --from <rev1> --to <rev2>` |
| Integrate fix | `git cherry-pick <sha>` | `jj rebase -r <change-id> -o <target>` |
| Merge to main | `git checkout main && git merge <branch>` | `jj rebase -s <rev> -o main --skip-emptied` |
| Delete branch/bookmark | `git branch -d <name>` | `jj bookmark delete <name>` |
| Force delete | `git branch -D <name>` | `jj abandon <rev>` + `jj bookmark delete <name>` |
| Current location | `git branch --show-current` | `jj log -r @ --no-graph -T 'change_id.short(8)'` |
| Status | `git status` | `jj st` |

## Workspace Path Convention

All workspaces use the **sibling directory** pattern to avoid confusing LSP servers:

```text
<repo>/                    # main repo
<repo>_worktrees/          # workspace parent (sibling)
  feature-auth/            # one workspace per task
  fix-bug-123/
```

## jj-Specific Rules

When VCS is jj, follow these additional rules:

- Always `jj git fetch` at the start of any task
- Always `jj commit -m "..."` before `jj new` — `jj new` moves `@` and files
  in the old change leave the working directory (lost-work footgun)
- Use **change IDs** (not commit hashes) — they survive rewrites
- Do NOT `jj describe` or rewrite commits that have been pushed
- Use `--skip-emptied` for cleanup rebases (auto-abandons empty commits)
- Prefer `jj rebase --skip-emptied` over manual `jj abandon`
- `@` is the empty working-copy commit; use `@-` for the meaningful committed
  state when verifying or reviewing

## Note on jj Rebase Flag

The destination flag for `jj rebase` is `-o` / `--onto` (not `-d` /
`--destination`, which is deprecated). All examples in this file use `-o`.
