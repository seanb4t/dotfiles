# jj Agent-Friendly Configuration

Recommended jj configuration for non-interactive agent environments.
Cherry-pick what applies to your setup.

## User-Level Config (`~/.config/jj/config.toml`)

```toml
#:schema https://docs.jj-vcs.dev/latest/config-schema.json

[user]
name = "your-name"
email = "your-email@example.com"

[ui]
# Disable pager -- agents can't interact with less/more
paginate = "never"

# No-op diff editor -- prevents jj split from opening an editor
diff-editor = ":"

# No-op merge editor -- prevents jj resolve from opening a tool
# (agents MUST edit conflict markers directly)
merge-editor = ":"

[templates]
# Readable auto-generated bookmark names for --change pushes
# Default is "push-" ++ change_id.short()
git_push_bookmark = '"push-" ++ change_id.short()'

# Comfortable log format (less dense than default)
# log = "builtin_log_comfortable"

[template-aliases]
# Shortest unique IDs (saves horizontal space in logs)
# 'format_short_id(id)' = "id.shortest()"

[snapshot]
# Max file size for auto-tracking new files (default 1 MiB)
# Increase if agents generate large artifacts (test fixtures, data files)
max-new-file-size = "10MiB"

[aliases]
# Daily sync: fetch + rebase onto main, auto-abandon landed commits
sync = ["util", "exec", "--", "sh", "-c", "jj git fetch && jj rebase -o main --skip-emptied"]

# Move closest bookmark to current change (the "forgot to advance" fix)
tug = ["bookmark", "move", "--from", "heads(::@ & bookmarks())", "--to", "@"]

# Abandon local commits whose content already landed in main
landed = ["abandon", "-r", "ancestors(bookmarks()) & ~ancestors(main)"]
```

## Repo-Level Config (`.jj/repo/config.toml`)

Use for per-repo settings that differ from your user defaults.

```toml
[git]
# Which remotes to fetch from (order matters)
fetch = ["origin", "upstream"]

# Which remote to push to
push = "origin"

# Write change IDs into Git commit headers (preserved by GitHub/GitLab).
# Enables change ID references in PR comments that survive squash-merge.
write-change-id-header = true

[revset-aliases]
# Custom trunk definition (if your main branch isn't main/master/trunk)
# 'trunk()' = 'your-branch@your-remote'

# Custom immutable heads (e.g., protect release branches too)
# 'immutable_heads()' = 'trunk() | tags() | untracked_remote_bookmarks() | "release-*"'

# Useful aliases for agents
'my-stack' = 'reachable(@, mutable())'
'unpushed' = 'bookmarks() ~ remote_bookmarks()'
'stale-bookmarks' = 'bookmarks() & ancestors(trunk()) & ~trunk()'
```

## Template Customization

```toml
[template-aliases]
# Shortest unique IDs -- saves horizontal space in agent logs
'format_short_id(id)' = "id.shortest()"

# Compact author display
'format_short_signature(signature)' = '''
  coalesce(
    if(signature.email() == config("user.email").as_string(),
       label("author me", "(me)")),
    signature.username(),
    email_placeholder
  )
'''
```

## Watchman Integration (Large Repos)

For repos with 10k+ tracked files, enable Watchman to avoid full directory
scans on every jj command.

```toml
[fsmonitor]
# Requires watchman to be installed (brew install watchman)
backend = "watchman"

# Auto-snapshot on filesystem changes (background daemon)
# watchman.register-snapshot-trigger = true
```

## Key Config Decisions for Agents

| Setting | Why It Matters |
|---------|---------------|
| `paginate = "never"` | Agents can't interact with pagers |
| `diff-editor = ":"` | Prevents `jj split` from blocking |
| `merge-editor = ":"` | Prevents `jj resolve` from blocking |
| `max-new-file-size` | Controls whether large generated files are tracked |
| `sync` alias | One-command daily reconciliation |
| `tug` alias | Prevents stale bookmark pushes |

## Environment Variables

| Variable | Use |
|----------|-----|
| `JJ_CONFIG` | Override config file location |
| `JJ_USER` | Override user.name |
| `JJ_EMAIL` | Override user.email |
| `JJ_TIMESTAMP` | Override commit timestamp (useful for reproducible tests) |
| `JJ_RANDOMNESS_SEED` | Deterministic change IDs (useful for testing) |
