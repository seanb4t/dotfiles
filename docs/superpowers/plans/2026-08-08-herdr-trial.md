# herdr trial

**Branch:** `trial/herdr` · **Date:** 2026-08-08 · **Status: ADOPTED — herdr is
the default multiplexer.** tmux stays installed and configured as a fallback and
reference; `echo tmux > ~/.local/state/mux` returns to it for new windows.

Adopted the same day the trial started, on the strength of criteria 1–3 plus
hands-on use. What decided it: native per-pane agent session restore (the thing
tmux-resurrect would have needed a frozen upstream and four workarounds to
approximate), and the sidebar replacing four hand-written attention scripts.
The accepted regression is unchanged — non-agent processes do not relaunch.

Evaluating [herdr](https://herdr.dev) as a replacement for the Ghostty+tmux agent
cockpit described in `../specs/2026-06-13-ghostty-tmux-agent-cockpit-design.md`.

## Why this exists

The session that produced this was originally scoped to "restore tmux on reboot,
pick Claude sessions back up". That investigation concluded:

- `claude --continue` / newest-transcript-for-cwd is unreliable here. Measured
  **192 one-hour windows in 7 days with multiple live sessions in the same
  project directory**, peaking at 17. Correct resume needs per-pane session
  identity captured at launch, not a path lookup. (engram `pkqhgsp5bx`)
- tmux-resurrect can host that, but is frozen upstream since 2023-03 and needs
  four separate workarounds for this setup. (engram `z1af41rmyw`, `vrdhpz5xx1`)
- herdr implements exactly that architecture natively and on by default.
  (engram `k5vw9zkpr6`)

herdr is 25.8k stars in 4.5 months, Apache-2.0, Rust, in homebrew-core, shipping
daily — but **v0.8.0**, 138 open issues, and ~1110 of ~1300 commits from a single
author. Mature enough to trial, not proven enough to adopt blind.

## What adoption would delete

Not additive — herdr **replaces** tmux. Agent detection does not see through a
tmux pane (herdr sees `tmux` as the foreground process). If this is adopted:

| Retired | Replaced by |
|---|---|
| `dot_local/bin/claude-attention-count` | native `blocked`/`working`/`idle`/`done` + sidebar rollups |
| `dot_local/bin/claude-tmux-notify` | same |
| `dot_local/bin/tmux-jump-needy` | same |
| OSC 9/777 notification workaround (engram `mkex4cxrzw`, `y0wg39g18v`) | native notifications |
| `dot_local/bin/ghostty-tmux` grouped-session wrapper | herdr server + workspaces |
| the whole tmux-resurrect plan | native agent session restore |

And would need rebuilding: catppuccin macchiato theming, `C-Space` prefix,
scratch popups (`prefix g`/`G`), the sesh picker (`prefix o` / `M-s` — sesh is
tmux-only), extrakto, tmux-fingers, the which-key menu, `keys.md`.

## Known regression

herdr snapshot restore does **not** relaunch arbitrary processes — no `k9s`,
`nvim`, dev servers, or test watchers. Those panes return as fresh shells in
their saved cwd. tmux-resurrect's `@resurrect-processes` allow-list is strictly
better on that axis. Mitigating: the herdr server survives detach, network loss
and lid-close, so snapshot restore only happens on a real reboot.

## Setup gotcha: the chezmoi conflict

`herdr integration install claude` writes `~/.claude/hooks/herdr-agent-state.sh`
and **updates `~/.claude/settings.json`**.

- `.claude/hooks/` is **not** chezmoi-managed → safe.
- `.claude/settings.json` **is** chezmoi-managed (`dot_claude/settings.json`) →
  the next `chezmoi apply` reverts herdr's hook entries and silently kills
  session restore, i.e. the exact thing under test.

Handle it in this order:

```bash
herdr integration install claude
chezmoi diff ~/.claude/settings.json     # inspect what herdr added
chezmoi add ~/.claude/settings.json      # adopt it into the source state
herdr integration status                 # expect Claude Code >= 6
```

Do not skip the `chezmoi add` — a passing trial that silently stops passing
after an unrelated `chezmoi apply` is the worst outcome available here.

## Setup gotcha 2: herdr rewrites its own config.toml

Confirmed 2026-08-08. Changing anything in herdr's settings UI **appends to
`~/.config/herdr/config.toml`** — observed with `[ui.toast] delivery` and
`[ui] show_agent_labels_on_pane_borders`. So the file has two writers, exactly
like `~/.claude/settings.json`.

chezmoi fails safe here: `chezmoi apply` refuses with *"has changed since
chezmoi last wrote it"* rather than clobbering. But note the trap — a
`herdr server reload-config` after a refused apply reloads the **old** config,
so it can look like a config change had no effect.

Policy for this trial: **config.toml is chezmoi-owned.** After using the
settings UI, fold the change back into `dot_config/herdr/config.toml` by hand
(or `chezmoi add`), then:

```bash
HERDR_CONFIG_PATH=dot_config/herdr/config.toml herdr config check
chezmoi apply --force ~/.config/herdr
herdr server reload-config
```

Only use `--force` once the UI's changes are actually merged into source.

## Plugins

534 repos carry the `herdr-plugin` topic. Shortlist below is limited to ones
that close a gap this migration opens — adding more would confound the trial.

| Plugin | ★ | Replaces |
|---|---|---|
| [thanhdat77/herdr-navigator](https://github.com/thanhdat77/herdr-navigator) | 62 | the sesh picker (`prefix o` / `M-s`) — jump to workspace/agent/project/directory |
| [iurysza/termscope](https://github.com/iurysza/termscope) | 39 | extrakto + tmux-fingers — open files/links visible on screen |
| [devashish2203/herdr-worktrunk](https://github.com/devashish2203/herdr-worktrunk) | 81 | nothing, but this setup lives in `.worktrees/` checkouts |
| [nicosuave/memex](https://github.com/nicosuave/memex) | 89 | nothing — transcript search across Claude/Codex/Pi. No tmux equivalent, and this machine has ~2250 sessions per fortnight |

Deliberately **not** installing `vim-herdr-navigation` / `herdr-splits.nvim`:
vim-tmux-navigator was dropped from this setup on purpose (engram `ys4ahaca16`)
in favour of native directional binds, and `[keys] focus_pane_*` restores
`alt+hjkl` here.

**Trust:** plugins are unsandboxed — they run as your user with full Herdr CLI
access, and herdr neither reviews nor sandboxes them. `herdr plugin install`
previews the source and commands in an interactive terminal; use `--ref` to pin
a revision. Given this repo's public/no-plaintext-secrets posture, read the
`herdr-plugin.toml` before confirming any install.

## Ghostty integration

Ghostty's `command` is a single global value, so pointing it at herdr is a full
cutover, not a setting you dip into. During the trial it points at a dispatcher
instead:

```
command = ~/.local/bin/ghostty-mux     # reads ~/.local/state/mux
```

`ghostty-mux` defaults to **tmux**, so this branch behaves exactly like `main`
until deliberately flipped:

```bash
echo herdr > ~/.local/state/mux   # new Ghostty windows attach herdr
echo tmux  > ~/.local/state/mux   # back to tmux
rm ~/.local/state/mux             # same as tmux
```

Existing windows keep whatever they launched with, so a herdr window and a tmux
window can sit side by side.

### Server lifecycle inverts

This is the real architectural difference, not a detail. `ghostty-tmux` lazily
creates the tmux server on first window — correct for tmux, where a server with
no client is pointless. herdr's premise is the opposite: the server runs whether
or not anyone is attached. So the server should be owned by launchd, not by the
terminal:

```bash
brew services start herdr
```

Consequence: **restore happens at login, not at first-terminal-open.** That is
the thing to watch in criterion 2 — a Claude resume firing at login, before the
keychain and 1Password agent are necessarily up, is a different risk profile
than resuming when you open a terminal. If that bites, the fallback is to not
run the service and let `ghostty-mux` start the server on first window.

## Validation criteria

Trial fails if any of 1–4 fail. 5–7 are cost questions, not correctness.

1. **Per-pane resume under real load.** Two agents in the *same* worktree, both
   mid-conversation. `herdr server stop`, restart, reattach. Both must resume
   their own conversation. This is the criterion `--continue` fails.
2. **Reboot, not just restart.** Full macOS reboot with several workspaces open.
   Layout, cwd, and agent sessions come back.
3. **Nothing silently reverts.** Run `chezmoi apply` after setup, then repeat
   test 1. Catches the settings.json conflict above.
4. **Shift+Enter / CSI-u under Ghostty.** There is an open herdr issue in this
   family; tmux.conf currently needs `bind -n S-Enter send-keys Escape "[13;2u"`.
   Determine whether an equivalent workaround exists.
5. **fish + PATH inside panes.** `shell_mode = "auto"` should give login shells;
   confirm Homebrew PATH is sane in a fresh pane.
6. **The picker gap.** Decide whether workspaces + sidebar actually replace the
   sesh picker for the ~30-directory rotation, or whether that is a real loss.

### Not a criterion: multi-window mirroring

Resolved 2026-08-08 — `ghostty-tmux` mirrors on new windows in practice, and
herdr does too, so this is parity rather than a regression. Accepted as-is.

Note the comment block in `dot_local/bin/executable_ghostty-tmux` still claims
later windows are "NOT mirrored"; that comment is inaccurate and is a separate
cleanup, untouched by this branch.

## Rollback

Delete the branch. tmux config is untouched by this branch; the only live-system
changes are `brew install herdr`, `~/.config/herdr/`, and the Claude hook entries
(`herdr integration uninstall claude`, then `chezmoi apply` to restore
`settings.json`).

## Notes

- `docs/adr/` is **not** the home for this. That directory is generated from
  beads and is marked do-not-edit-by-hand; beads is no longer in use here, so
  the ADR pipeline is dormant and CLAUDE.md's beads section is stale.
- Nothing in `dot_config/tmux/` is modified on this branch. Coexistence is
  deliberate: herdr and tmux run as separate servers and never nest.
