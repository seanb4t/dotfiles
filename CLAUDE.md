# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A chezmoi-managed dotfiles repository. Files here map to `~/` via chezmoi's naming conventions:
- `dot_` prefix → `.` (e.g., `dot_config/` → `~/.config/`)
- `private_` prefix → restricted permissions
- `encrypted_*.age` → age-encrypted files decrypted at apply time
- `.tmpl` suffix → Go templates rendered with chezmoi data
- `symlink_` prefix → symlinks
- `executable_` prefix → executable permission

## Commands

```bash
chezmoi apply                    # Apply all changes to ~/
chezmoi apply --dry-run          # Preview what would change
chezmoi diff                     # Show pending changes
chezmoi edit <target>            # Edit a managed file (opens source)
chezmoi add <file>               # Add a new file to management
chezmoi add --encrypt <file>     # Add with age encryption
chezmoi execute-template < file  # Test template rendering
chezmoi cat-config               # Show resolved config values
```

## Architecture

### Secrets Flow

Two-tier system, both requiring 1Password CLI (`op`) authenticated:

1. **Dynamic secrets** — `onepasswordRead("op://vault/item/field")` in `.tmpl` files. Fetched at apply time, never stored in repo.
2. **Encrypted files** — `encrypted_*.age` files decrypted with age key at `~/.config/age-keys.txt`.

### Template Data Sources

- **`.chezmoi.toml.tmpl`** — Main config. Defines `hostname`, `personal.*`, `git.*`, `ssh_agent.*`, `vault.*` data. Personal fields pulled from 1Password.
- **`.chezmoidata/mac-defaults.yaml`** — macOS `defaults write` commands (Finder, Dock, screensaver, etc.)
- **`.chezmoidata/cargo-crates.yaml`** — Rust crates to install.
- **Chezmoi builtins** — `.chezmoi.os`, `.chezmoi.hostname`, `.chezmoi.arch`, `.chezmoi.homeDir`.

### Script Execution Order

Scripts in `.chezmoiscripts/` run in phases, then alphabetically by name within each phase:

| Phase | Purpose | Example |
|-------|---------|---------|
| `run_before_` | Prerequisites & validation | Validate 1Password auth, create SSH dirs |
| `run_once_` | One-time setup | Set user shell, GitHub auth, fisher install |
| `run_onchange_` | Content-hash triggered | Brew bundle, macOS defaults, TPM plugins |
| `run_after_` | Post-apply tools | Rustup, kubeswitch, atuin login, Claude CLI |

**Hash triggers**: `run_onchange_` scripts embed content hashes to auto-re-run when source files change:
```bash
# packages hash: {{ include "dot_Brewfile" | sha256sum }}
```

### Platform Conditionals

Most scripts and templates use `{{ if eq .chezmoi.os "darwin" }}` / `"linux"`. Primary target is macOS. Machine-specific behavior keys off `.chezmoi.hostname` (e.g., SSH configs, power settings, git signing).

### Key Directories

| Path | Content |
|------|---------|
| `dot_config/fish/` | Fish shell config (fisher plugins, conf.d for grc/direnv/atuin/op-cli) |
| `dot_config/herdr/` | herdr config — **the default multiplexer** |
| `dot_config/tmux/` | tmux config (Catppuccin Macchiato, vendored plugins, sesh) — fallback only |
| `dot_config/ghostty/` | Ghostty terminal config; `command` runs `ghostty-mux` |
| `private_dot_ssh/` | SSH configs with per-host includes (`config.<hostname>.tmpl`) |
| `dot_kube/` | Kubernetes configs, mostly age-encrypted |
| `.chezmoiscripts/` | All lifecycle scripts |

### Multiplexer: herdr (since 2026-08-08)

herdr replaced tmux as the default. tmux stays installed and configured as a
fallback and reference.

- **Switching**: `dot_local/bin/ghostty-mux` dispatches on `~/.local/state/mux`.
  Default (no file) is herdr; `echo tmux > ~/.local/state/mux` sends *new*
  Ghostty windows to the old `ghostty-tmux` wrapper. Existing windows keep
  whatever they launched with.
- **Server**: runs via `brew services` (RunAtLoad + KeepAlive), so it survives
  reboot and restore happens at login, not at first-terminal-open.
- **Config**: `herdr config check` validates (honours `HERDR_CONFIG_PATH`, so it
  can check the chezmoi source without touching the live system);
  `herdr server reload-config` applies to a running server. Invalid values do
  **not** fail loudly at runtime — they fall back to a default with a startup
  warning — so always run `config check` after editing.
- **Gotcha**: herdr's settings UI *writes back* to `~/.config/herdr/config.toml`,
  so it fights chezmoi. `chezmoi apply` refuses rather than clobbering, but a
  `reload-config` after a refused apply silently reloads the old config. Fold UI
  changes back into `dot_config/herdr/config.toml`, then `apply --force`.
- **Agent guidance**: <https://herdr.dev/agent-guide.md> for setup and
  troubleshooting. Controlling herdr *from inside a pane* is the vendored
  `herdr` skill (`.agents/skills/herdr/`), which self-gates on `HERDR_ENV=1` —
  do not duplicate its content into any CLAUDE.md.

### External Dependencies

Defined in `.chezmoiexternal.toml`:
- `kubie.fish` completion — fetched from GitHub, refreshed weekly.
- herdr agent skill, catppuccin/tmux, extrakto — pinned to immutable commits/tags.

### Ignored Files

`.chezmoiignore` excludes: `README.md`, `AGENTS.md`, `iterm/`,
`**/fish_variables`, `**/*.bak`.

Note it does **not** exclude `CLAUDE.md` or `.claude/`, despite what earlier
revisions of this file claimed. Consequence: this file is applied to
`~/CLAUDE.md`, where it is loaded for every project under `~` — so keep it
scoped to facts that survive that blast radius. Global *coding* instructions
belong in `dot_claude/CLAUDE.md` (`~/.claude/CLAUDE.md`) instead.

## Conventions

- **Script naming**: `run_[phase]_[order]_[name].[ext].tmpl` — numeric ordering controls execution sequence within phase.
- **Brewfiles**: `dot_Brewfile` (core), `dot_Brewfile-linux` (Linux-only), `dot_Brewfile-mas` (App Store).
- **SSH config**: Modular — main `config.tmpl` conditionally includes `config.<hostname>.tmpl` files.
- **Git LFS**: `.gitattributes` tracks most file types through LFS (templates, scripts, configs, encrypted files).

## Prerequisites for `chezmoi apply`

1. 1Password CLI (`op`) installed and authenticated — `run_before_validate_1password.sh.tmpl` blocks on this.
2. Age encryption key at `~/.config/age-keys.txt`.
3. Homebrew installed.

## Gotchas

- `chezmoi apply` stops on script failure — use `chezmoi apply ~/.config/fish/` to apply specific paths without triggering unrelated `run_onchange_` scripts (e.g., brew bundle).
- `fisher update` updates all *installed* plugins, not just `fish_plugins`. To remove old plugins: update `fish_plugins` → `chezmoi apply ~/.config/fish/` → `fisher remove <old>` → `fisher install <new>`.
- Fish `conf.d/` loads alphabetically — `00_` prefix ensures pre-configuration runs first.
- tmux `extended-keys` sends xterm-style encoding; apps expecting CSI u (e.g., Claude Code for Shift+Enter) need explicit keybind translation in tmux.conf. (tmux-only; herdr does not use this mechanism.)
- sesh picker: use `run-shell` + `fzf-tmux -p`, never `display-popup` wrapping `fzf-tmux -p` (double popup). (tmux-only; sesh does not work with herdr — its equivalent is `prefix+g`, the session navigator.)
- herdr keybinds: `herdr config check` validates syntax but does **not** detect collisions — it returns `ok` for a `[[keys.command]]` that shadows a built-in action. Scan new binds against `herdr --default-config` by hand.
- herdr vs tmux split vocabulary is inverted: herdr's `split_vertical` is a *right* split (vim/zellij convention), tmux's `split-window -h` is the same shape. The CLI is unambiguous — `herdr pane split --direction right|down`.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
