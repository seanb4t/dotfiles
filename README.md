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

## Secrets

All secrets are pulled from 1Password at apply time. Ensure `op` is authenticated before running chezmoi.
