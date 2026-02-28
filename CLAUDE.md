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
| `dot_config/fish/` | Fish shell config, 20+ fisher plugins |
| `dot_config/tmux/` | tmux config (Catppuccin Macchiato, 8 plugins) |
| `private_dot_ssh/` | SSH configs with per-host includes (`config.<hostname>.tmpl`) |
| `dot_kube/` | Kubernetes configs, mostly age-encrypted |
| `.chezmoiscripts/` | All lifecycle scripts |

### External Dependencies

Defined in `.chezmoiexternal.toml`:
- `kubie.fish` completion — fetched from GitHub, refreshed weekly.

### Ignored Files

`.chezmoiignore` excludes: `README.md`, `AGENTS.md`, `CLAUDE.md`, `.claude/`, `iterm/`, `**/fish_variables`, `**/*.bak`.

## Conventions

- **Script naming**: `run_[phase]_[order]_[name].[ext].tmpl` — numeric ordering controls execution sequence within phase.
- **Brewfiles**: `dot_Brewfile` (core), `dot_Brewfile-linux` (Linux-only), `dot_Brewfile-mas` (App Store).
- **SSH config**: Modular — main `config.tmpl` conditionally includes `config.<hostname>.tmpl` files.
- **Git LFS**: `.gitattributes` tracks most file types through LFS (templates, scripts, configs, encrypted files).

## Prerequisites for `chezmoi apply`

1. 1Password CLI (`op`) installed and authenticated — `run_before_validate_1password.sh.tmpl` blocks on this.
2. Age encryption key at `~/.config/age-keys.txt`.
3. Homebrew installed.
