# Sean's Dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

## Prerequisites

- **1Password CLI** (`op`) - signed in and configured
- **age encryption key** at `~/.config/age-keys.txt`
- **Homebrew** installed

## Setup

```bash
chezmoi init --apply git@github.com:seanb4t/dotfiles.git
```

You'll be prompted for the machine hostname on first run.

## Machine Notes

Power settings vary by machine:
- `magellan`/`denver`: Disable sleep, 30-minute display timeout
- Other machines: 10-minute timeouts for sleep, disk, and display

## Terminal Setup

**Terminal Emulator:** [Ghostty](https://ghostty.org/) with JetBrainsMono Nerd Font

**Multiplexer:** [tmux](https://github.com/tmux/tmux) with [TPM](https://github.com/tmux-plugins/tpm)
- Prefix: `Ctrl+a`
- Config: `~/.config/tmux/tmux.conf`
- Theme: [Catppuccin Macchiato](https://github.com/catppuccin/tmux)

**Plugins:**
| Plugin | Description |
|--------|-------------|
| [tmux-sensible](https://github.com/tmux-plugins/tmux-sensible) | Sensible defaults |
| [tmux-resurrect](https://github.com/tmux-plugins/tmux-resurrect) | Session persistence |
| [tmux-continuum](https://github.com/tmux-plugins/tmux-continuum) | Auto-save/restore |
| [tmux-command-palette](https://github.com/lost-melody/tmux-command-palette) | Fuzzy command finder |
| [tmux-floating-terminal](https://github.com/lloydbond/tmux-floating-terminal) | Popup terminal |
| [tmux-fingers](https://github.com/Morantron/tmux-fingers) | Vimium-style copy |
| [tmux-click-copy](https://github.com/aless3/tmux-click-copy) | Click to copy |
| [tmux-easymotion](https://github.com/ddzero2c/tmux-easymotion) | Easymotion navigation |

**Install plugins:** `Ctrl+a I` (after starting tmux)

## Secrets

All secrets are pulled from 1Password at apply time. Ensure `op` is authenticated before running chezmoi.
