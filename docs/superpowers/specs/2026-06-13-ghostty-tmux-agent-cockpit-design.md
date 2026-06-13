# Design: Ghostty + tmux keyboard-native agent cockpit (cmux-coexist)

- **Bead:** chezmoi-6an
- **Date:** 2026-06-13
- **Status:** Design — pending design-reviewer
- **Author:** Sean (with Claude Opus 4.8)

## 1. Context & goal

Today's daily driver is **cmux.app** — a native macOS terminal built on *libghostty*
(the same engine Ghostty uses, consumed as a library) that bundles terminal +
multiplexing (vertical-tab workspaces + split panes) + an embedded scriptable
browser + a socket/CLI control plane + first-class agent-attention notifications.
It is **not** a multiplexer you run inside a terminal, and Ghostty does not attach
to it; it is a sibling app to Ghostty.

The goal is to migrate to the classic two-layer stack — **Ghostty.app (terminal) +
tmux (multiplexer)** — while **keeping cmux.app installed** as a fallback (coexist).
Both apps read `~/.config/ghostty/config` for terminal behaviour, so terminal
look-and-feel carries over unchanged.

This is a **from-scratch** tmux config. The existing `dot_config/tmux/tmux.conf` is
*not* treated as authoritative; every option and plugin below is justified and its
upstream verified current/maintained as of 2026-06-13.

### What we keep, concede, and rebuild

| cmux capability | Disposition in ghostty+tmux |
|---|---|
| GPU render, native, no Electron | **Parity** — Ghostty *is* libghostty |
| Split panes | **Parity** — native tmux panes |
| Scriptable refs / events / control | **Parity+** — the tmux server *is* a socket API (`%pane_id`, hooks, `pipe-pane`, control-mode); the existing `drain-worker-launch`/`_muxdriver.py` already drive tmux this way |
| Vertical-tab workspaces w/ rich sidebar (branch, ports, PRs, progress) | **Conceded to "good enough"** — tmux windows + sesh + enriched window labels; ports/PRs/progress dropped |
| **Agent-attention notifications** (rings, dock badge, OSC 9/99/777) | **Rebuilt** — this is the center of gravity (Layer 3) |
| Embedded scriptable browser | **Conceded** — external browser; extrakto/fingers open URLs |
| `cmux diff --last-turn` | **Conceded as a terminal feature** — `jj diff`/`lazygit`/`delta` |
| Cloud agent VMs (`cmux vm`) | **Conceded** — orthogonal; Claude Code has its own sandbox |

### Workflow facts driving the design (from transcript/history mining)

- Autonomous `/drain` workers are **ephemeral and fire-and-forget**: spawned on
  demand into a detached surface, torn down on completion. The operator walks away
  and reacts to a notification, then checks back via `bd show`. No persistent
  multi-pane cockpit is watched.
- Epic drains carry ~20 beads but each worker is an isolated cold-boot Claude
  session in its own jj worktree.
- Editing is **not** done in nvim/lvim splits inside tmux — Claude Code is the
  primary "editor." (Justifies dropping `vim-tmux-navigator`.)
- Past tmux friction was specific: `ctrl-k`/`shift-enter` keybinds and Ghostty
  launching tmux in every pane — both already understood and handled.

## 2. Grounding & currency (every choice justified)

Verified 2026-06-13 via GitHub API (`pushed_at`, latest release, archived), DeepWiki
(Ghostty OSC behaviour), Context7 (`/tmux/tmux`), and a web sweep (sources inline).

| Component | Evidence | Verdict | Decision |
|---|---|---|---|
| tmux **3.6b** | repo pushed 2026-06-13; installed == latest release (2026-05-20) | CURRENT | Base; build to 3.6 |
| **catppuccin/tmux** | latest tag **v2.3.0** (2026-04-08); user on v2.1.3 | CURRENT | Adopt v2.3.0 |
| **sesh** | brew formula stable **2.26.2** (bottled); very active | CURRENT | Core switcher (Brewfile) |
| **tmux-fingers** (Morantron) | pushed 2026-06-09; latest tag **2.7.1**; *not* on crates.io; no brew formula | CURRENT | Hint-copy; vendor + cargo build |
| **extrakto** (laktak) | pushed 2026-03-02; **no release tags**; no brew formula | CURRENT | Fuzzy extract/insert/url; vendor pinned to a commit SHA |
| **Ghostty** | pushed 2026-06-10; native OSC 9 + OSC 777 → Notification Center (`desktop-notifications=true` default) | CURRENT | Notification sink |
| tmux-resurrect + continuum | ~22 mo idle; 287/92 open issues | STALE | **Drop** → sesh-first |
| fcsonline/tmux-thumbs | release 2023; 2 yr idle | STALE | **Replace** → tmux-fingers |
| tmux-yank | release **2018** | STALE | **Don't add** → native OSC-52 |
| terminal-notifier / alerter | deprecated `NSUserNotificationCenter`; **breaks on macOS 26 (user is Darwin 27)** | BROKEN-ON-OS | **Drop** → Ghostty OSC |
| vim-tmux-navigator | active (2026-01) but workflow doesn't use nvim-in-tmux | N/A | **Drop** → native `M-hjkl` |
| TPM | active (2026-05) | CURRENT but | **Not used** → chezmoi-vendored (fork 1) |

### Key mechanism findings

1. **Ghostty notifications (DeepWiki, authoritative).** Ghostty parses OSC 9 and
   OSC 777 into macOS Notification Center alerts via `UNUserNotificationCenter`
   (modern API). `desktop-notifications` defaults true. OSC 9 form:
   `printf '\x1b]9;<body>\x07'`; OSC 777 carries title+body. Bonus native option:
   `notify-on-command-finish`.
2. **tmux has NO native OSC 9/777 handling.** Maintainer declined OSC 777; OSC 9
   only "on todo" (tmux/tmux#5136, 2026-06-07). Passthrough is the generic answer:
   `allow-passthrough on` (value `all` also fires from *inactive* panes) +
   DCS-wrap to the pane TTY.
3. **Claude Code v2.1.139+ `terminalSequence` hook field (supersedes the TTY hack).**
   Hooks now run with **no controlling terminal**; a hook returns
   `{"terminalSequence":"<OSC>"}` and Claude Code emits it through its own write
   path — allowlisted to OSC 0/1/2/9/99/777 + BEL, **race-free, and it performs the
   tmux passthrough wrapping itself.** Source: code.claude.com/docs/en/hooks. This
   is the official, current mechanism and is what the attention loop uses.
4. **Clipboard (tmux Clipboard wiki + 2026 OSC-52 guidance).** Current best practice
   on macOS+Ghostty is native OSC-52: `set -s set-clipboard on` **plus**
   `set -g allow-passthrough on` (so DCS-wrapped OSC-52 from nvim/Claude is honoured).
   SSH-portable. `tmux-yank` unnecessary.
5. **catppuccin v2 API gotcha.** Theme colours are tmux options
   (`#{@thm_*}`), status modules append via `#{E:@catppuccin_status_*}`. The
   `directory`/`application` modules **freeze** if defined with `-gF`/`E:`
   expansion at definition time — set their `_text` plainly, expand only in
   `status-right` (issues #407/#527).
6. **sesh native picker.** `sesh picker` replaces the external fzf dependency:
   `display-popup -E "sesh picker -idH"` is a single popup — sidesteps the prior
   "fzf-tmux double-popup" gotcha entirely.

## 3. Design principles

1. **Keyboard-native; no mouse reporting.** tmux never enables mouse reporting;
   Ghostty owns the mouse. A live toggle exists for the rare dense-split copy.
2. **Everything current & maintained**, pinned where vendored.
3. **Notification-driven, not babysat.** The config's job is clean surface
   create/destroy and an unmissable "this one needs you" signal — not a cockpit.
4. **chezmoi-native & reproducible.** Plugins vendored at pinned refs; no
   interactive bootstrap.
5. **Coexist & reversible.** cmux.app untouched; rollback is "launch cmux."

## 4. Layer 1 — Base + mouse-off + clipboard + copy tiers

### 4.1 Base (native, tmux 3.6)
- Prefix **`C-a`** with `bind C-a send-prefix` (double-tap sends literal `^A`,
  preserving readline start-of-line). *Rationale:* muscle memory; `send-prefix`
  mitigates the readline clobber. (`C-Space` is the noted alternative.)
- `set -g base-index 1`, `setw -g pane-base-index 1`, `set -g renumber-windows on`.
- `set -g focus-events on`, `set -sg escape-time 0`, `set -g history-limit 50000`.
- `set -g default-terminal "tmux-256color"`,
  `set -as terminal-features ",xterm-256color:RGB"` (truecolor; `-as` append, no dup).
- **Shift+Enter for Claude Code:** retain the known-good
  `bind -n S-Enter send-keys Escape "[13;2u"` (CSI-u). *Empirical-validation note:*
  tmux 3.5 revamped extended-keys (mode 2, `extended-keys-format`,
  `extended-keys "always"`); a cleaner `extended-keys on` + `extended-keys-format
  csi-u` may obviate the manual bind, but it is terminal-dependent — validate at
  implementation; keep the manual bind as the safe default.
- `bind r source-file ~/.config/tmux/tmux.conf \; display "reloaded"`.

### 4.2 Mouse-off + toggle
- `set -g mouse off` — Ghostty owns the mouse (no mouse reporting, the explicit
  requirement). Consequence: wheel no longer scrolls a pane (scrollback is
  keyboard copy-mode); Ghostty native selection works but crosses tmux pane
  borders (it sees one grid).
- `bind m set -g mouse \; display "mouse #{?mouse,on,off}"` — live escape hatch for
  the occasional side-by-side drag-copy.

### 4.3 Clipboard (native OSC-52)
- `set -s set-clipboard on` + `set -g allow-passthrough on`.
- Copy-mode-vi: `v` begin-selection, `y` `copy-selection-and-cancel` (honours
  `set-clipboard` → OSC-52 → Ghostty → system clipboard, SSH-portable).
- *Local-only alternative noted:* `copy-pipe-and-cancel "pbcopy"` if OSC-52 ever
  proves insufficient (do not combine both — they conflict).

### 4.4 Copy tiers (all keyboard-native)
1. **Ghostty native drag-select** (visible, instant) — `copy-on-select=true` already
   in ghostty config.
2. **copy-mode-vi** `prefix-[`, `/`search, `v`, `y` — pane-aware scrollback.
3. **tmux-fingers** (`prefix-F`) — hint-label every visible token (path/SHA/url/bd-id)
   → one letter copies; modifier variants paste/open.
4. **extrakto** (`prefix-Tab`) — fzf popup of tokens from pane+scrollback; fuzzy
   filter → insert into prompt / copy / open (subsumes URL-from-scrollback; replaces
   tmux-fzf-url).

## 5. Layer 2 — Keyboard-native switching (vertical-tab replacement)

Sessions = projects (one per repo/worktree, matching the jj-worktree-per-drain habit).

| Bind | Action | Notes |
|---|---|---|
| `prefix-o` / `M-s` | `display-popup -E "sesh picker -idH"` | sesh native picker; single popup |
| `prefix-w` | `choose-tree -Zw` | zoomed session→window tree (cmux `goToWorkspace` analog) |
| `M-1`…`M-9` | `select-window -t N` | direct window jump |
| `M-Tab` | `last-window` | alt-tab between two tasks |
| `M-[` / `M-]` | `previous-window` / `next-window` | |
| `M-h/j/k/l` | `select-pane -L/-D/-U/-R` | **native** (replaces vim-tmux-navigator) |
| `prefix-q` | `display-panes` | numbered pane jump |
| `prefix-N` | `command-prompt … new-session` | |
| `bind \|` / `bind -` | `split-window -h/-v -c "#{pane_current_path}"` | path-preserving splits |
| `bind c` | `new-window -c "#{pane_current_path}"` | |
| `bind -r H/J/K/L` | `resize-pane` | |

**Enriched window labels** (info-scent recovery): window-status shows
`index:basename(cwd)` + zoom/bell flags, e.g. `2:holomush ●`. Implemented with
`#{b:pane_current_path}` (cheap, no shell fork). Git-branch-per-window is a
per-redraw `#()` shell call → **maximal opt-in only**, not default.

## 6. Layer 3 — The attention loop (medium, room for maximal)

Two signal sources, deliberately separated.

### 6.1 Interactive Claude windows (hands-on) — the core
Wire Claude Code `Notification` and `Stop` hooks (in `dot_claude/settings.json`) to
a script `~/.local/bin/claude-tmux-notify`
(chezmoi: `dot_local/bin/executable_claude-tmux-notify`). The script:

1. Reads hook JSON from stdin (`jq`); extracts `.message` (Notification) or a
   "finished" body (Stop), and the session/cwd for context.
2. **Side effect (optional, runs via tmux socket — no TTY needed):** mark the
   calling window. The hook subprocess inherits `$TMUX_PANE`, so
   `tmux set-option -w -t "$TMUX_PANE" @needs_attention 1` is targetable. (Medium
   relies on the bell flag below; the user-option write is for maximal’s count.)
3. **Emit the desktop notification + window flag** by printing
   `{"terminalSequence": "<OSC-777 notify><BEL>"}` to stdout. Claude Code delivers
   it race-free through tmux:
   - OSC 777 → Ghostty Notification Center alert (`\x1b]777;notify;Claude Code;<body>\x07`).
   - the trailing **BEL** → tmux `monitor-bell on` lights the window's bell flag in
     the Catppuccin status bar. **No focus is stolen.**

`set -g monitor-bell on`, `set -g visual-bell off`, `set -g bell-action other`.

**Jump-to-needy:** `prefix-Tab` is taken by extrakto and `M-Tab` by last-window, so
bind `prefix-b` → helper that selects the next window with a bell flag:
```
tmux list-windows -F '#{window_bell_flag} #{window_index}' \
  | awk '$1==1{print $2; exit}' | xargs -r -I{} tmux select-window -t {}
```
Visiting the window clears the flag natively.

### 6.2 Autonomous drain workers — unchanged boundary
`/drain` workers remain governed by the existing `drain-watchdog` (reads the
surface, classifies `blocked-input`/`api-error`, fires `PushNotification`). The
Claude hook *also* fires inside workers (additive desktop notif + bell flag on the
detached worker window), but **the watchdog stays authoritative** for autonomous
epic drains. No change to `_muxdriver.py` / `drain-worker-launch`.

### 6.3 Medium vs maximal
- **Medium (this spec):** OSC-777 desktop notif + BEL window flag + `prefix-b`
  jump. Hook script is near-pure-stdout.
- **Maximal (appendix, additive):** `@needs_attention`/cache-dir writes feed a
  `#(claude-attention-count)` status segment and/or a dashboard window; OSC-9;4
  progress forwarding; click-to-teleport via a modern `UNUserNotificationCenter`
  notifier (NotifiCLI / terminal-notifier-next) — *only* if click-to-pane is ever
  wanted; not a dependency.

## 7. Plugin set & delivery (chezmoi-vendored, pinned)

**No TPM.** Plugins are vendored via `.chezmoiexternal.toml` (mirrors the existing
`kubie.fish` pattern) and loaded with `run-shell` at the bottom of `tmux.conf`.

| Plugin | Pin | Mechanism | Load line |
|---|---|---|---|
| catppuccin/tmux | tag **v2.3.0** | `.chezmoiexternal.toml` `type="git-repo"` | `run ~/.config/tmux/plugins/catppuccin/tmux/catppuccin.tmux` |
| extrakto | **commit SHA** (no tags exist) | `.chezmoiexternal.toml` archive at SHA | `run-shell ~/.config/tmux/plugins/extrakto/extrakto.tmux` |
| tmux-fingers | tag **2.7.1** | git-repo clone **+ cargo build** (not on crates.io / no brew) | `run-shell ~/.config/tmux/plugins/tmux-fingers/tmux-fingers.tmux` |
| sesh | brew **2.26.2** | `dot_Brewfile` (formula, bottled) | n/a (CLI binary) |

- **tmux-fingers build:** a `run_onchange_` script builds the Rust binary
  (`cargo build --release` in the plugin dir), gated on `cargo` availability
  (rustup is installed by an existing `run_after_` script). Content-hash trigger on
  the pinned tag. If `cargo` is absent at apply time, the script warns and skips;
  fingers degrades to "not loaded" without breaking tmux.
- **extrakto runtime deps:** `python3` + `fzf` (both present).
- **catppuccin v2.3.0** loaded with the v2 status-module shape (§2 gotcha #5).

Theme config (v2.3.0 shape):
```
set -g @catppuccin_flavor "macchiato"
set -g @catppuccin_window_status_style "rounded"
# directory/application: set _text plainly, expand only in status-right (no -gF/E:)
run ~/.config/tmux/plugins/catppuccin/tmux/catppuccin.tmux
set -g status-left ""
set -ag status-right "#{E:@catppuccin_status_session}"
```

## 8. chezmoi file manifest

| Path (source) | Change |
|---|---|
| `dot_config/tmux/tmux.conf` | Rewrite from scratch per §4–7 |
| `.chezmoiexternal.toml` | Add catppuccin (tag), extrakto (SHA), tmux-fingers (tag) |
| `dot_local/bin/executable_claude-tmux-notify` | **New** — hook notify script |
| `dot_claude/settings.json` | Add `Notification` + `Stop` hook entries calling the script |
| `dot_Brewfile` | Ensure `sesh` present (likely already installed) |
| `dot_config/ghostty/config` | Re-enable tmux auto-attach (`command = …tmux new-session -A -s main`); confirm `desktop-notifications` not disabled |
| `.chezmoiscripts/run_onchange_*_tmux-fingers-build.sh.tmpl` | **New** — gated cargo build of fingers |
| `dot_config/tmux/plugins/` | Add to `.chezmoiignore` (vendored externals, not source-managed) |

The prior plugins (resurrect, continuum, thumbs, fzf-url, vim-tmux-navigator, TPM)
are removed from config and external definitions.

## 9. Coexistence & rollback

- cmux.app and `~/.config/cmux/` are untouched; `cmux` CLI still works.
- Ghostty's shared `~/.config/ghostty/config` change (re-enabling the tmux
  `command`) affects **Ghostty.app only** — cmux manages its own surfaces and does
  not honour the `command` directive.
- Rollback = launch cmux instead of Ghostty; or comment the ghostty `command` line.

## 10. Verification plan (per layer)

Applied incrementally with `chezmoi apply ~/.config/tmux/` (scoped, avoids unrelated
`run_onchange_` scripts), then `tmux source-file`:

1. **Base/clipboard:** reload; confirm truecolor (`tmux info | rg RGB`), copy a line
   in copy-mode → paste into another app (OSC-52 roundtrip), toggle mouse with
   `prefix-m`.
2. **Switching:** `prefix-o` opens single sesh popup; `prefix-w` tree; `M-1..9`,
   `M-Tab`, `M-hjkl` pane nav; window labels show cwd basename.
3. **Plugins:** `prefix-F` (fingers hints appear → letter copies); `prefix-Tab`
   (extrakto popup; url filter opens a link); catppuccin renders with no frozen
   `directory` module.
4. **Attention loop:** in a Claude window, trigger a `Notification` (permission
   prompt) → Ghostty Notification Center alert appears **and** the window bell flag
   lights in the status bar; `prefix-b` jumps to it; flag clears on visit. Verify a
   detached worker window also flags without stealing focus.
5. **Coexist:** launch cmux → still functional; launch Ghostty → auto-attaches tmux.

## 11. Open risks / validate empirically

- **extended-keys modernization** (§4.1) — try `extended-keys "always"` +
  `extended-keys-format csi-u`; fall back to the manual `S-Enter` bind if any key
  regresses.
- **`terminalSequence` requires Claude Code ≥ v2.1.139** — confirm installed version;
  if older, fall back to the `allow-passthrough` + DCS-wrap-to-`#{pane_tty}` script
  path (documented, but second-choice).
- **tmux-fingers build** depends on cargo/rustup ordering at first apply; the gated
  `run_onchange_` build + graceful skip covers a cold machine.
- **extrakto SHA pin** must be refreshed deliberately (no upstream tags to track).

## 12. Maximal appendix (additive, out of scope for v1)

- `tmux-which-key` (active 2026-05) — discoverability popup for the keymap.
- `#(claude-attention-count)` status segment + dashboard window reading the
  attention cache dir.
- OSC-9;4 progress forwarding (tmux 3.6) → Ghostty progress indicator for Claude.
- Click-to-teleport notifications via a modern UNUserNotificationCenter CLI.
- Per-window git branch label (`#()` shell call) if the redraw cost is acceptable.
