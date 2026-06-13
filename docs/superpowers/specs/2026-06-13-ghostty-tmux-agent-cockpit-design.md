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
| **tmux-fingers** (Morantron) | **Crystal** (gh-api `language=Crystal`; `shard.yml`); pushed 2026-06-09; tag 2.7.1 live; **Homebrew tap `morantron/tmux-fingers`** (formula builds via `shards`, installs binary only) | CURRENT | Hint-copy; Brewfile tap, integrate via `load-config` |
| **extrakto** (laktak) | pushed 2026-03-02; **no release tags**; no brew formula | CURRENT | Fuzzy extract/insert/url; vendor pinned to a commit SHA via archive |
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
3. **Claude Code `terminalSequence` hook field (supersedes the TTY hack).**
   Hooks now run with **no controlling terminal**; a hook returns
   `{"terminalSequence":"<OSC>"}` and Claude Code emits it through its own write
   path — allowlisted to OSC 0/1/2/9/99/777 + BEL, **race-free, and it performs the
   tmux passthrough wrapping itself.** Source: code.claude.com/docs/en/hooks. The
   feature landed in the 2.1.14x series; the **installed Claude Code is 2.1.177**,
   which supports it — so this is validated against the live binary, not a guessed
   floor. This is the official, current mechanism and is what the attention loop uses.
4. **Clipboard (tmux Clipboard wiki + 2026 OSC-52 guidance).** Current best practice
   on macOS+Ghostty is native OSC-52: `set -s set-clipboard on` **plus**
   `set -g allow-passthrough on` (so DCS-wrapped OSC-52 from nvim/Claude is honoured).
   SSH-portable. `tmux-yank` unnecessary.
5. **catppuccin v2 API gotcha.** Theme colours are tmux options
   (`#{@thm_*}`), status modules append via `#{E:@catppuccin_status_*}`. The
   `directory`/`application` modules **freeze** if defined with `-gF`/`E:`
   expansion at definition time — set their `_text` plainly, expand only in
   `status-right` (issues #407/#527).
6. **sesh picker.** Verified live: `sesh 2.26.2` **does** expose a `picker`
   subcommand (`sesh picker [--flags] Interactive session picker`). However, the
   *proven* path is the operator's existing `~/.local/bin/sesh-picker.sh` — a rich
   `sesh list --icons | fzf-tmux -p` picker (all/tmux/config/zoxide/find/kill modes
   + preview) bound via **`run-shell`**, which respects the repo's documented
   "double-popup" gotcha (`run-shell` + `fzf-tmux -p`, never `display-popup`
   wrapping `fzf-tmux -p`). The native `sesh picker` in a `display-popup` is a noted
   simplification to evaluate, **not** adopted in v1.

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
- Prefix **`C-Space`** (`unbind C-b`; `set -g prefix C-Space`; `bind C-Space
  send-prefix`). *Rationale:* low-conflict — unlike `C-a` it does **not** clobber
  readline beginning-of-line in fish or Claude Code's input box (both places the
  operator lives), and it's ergonomic (thumb+pinky). Recent habit is prefix-free
  (cmux), so there is no entrenched `C-a` memory to preserve. `C-Space`'s only
  collision is CJK/IME toggles (N/A here). Alternatives: `C-a`+`send-prefix`
  (double-tap for literal `^A`) or default `C-b`.
- `set -g base-index 1`, `setw -g pane-base-index 1`, `set -g renumber-windows on`.
- `set -g focus-events on`, `set -sg escape-time 0`, `set -g history-limit 50000`.
- `set -g default-terminal "tmux-256color"`,
  `set -s terminal-features[1] "xterm-256color:RGB"` (truecolor; **indexed** form,
  not `-as` append — avoids stacking duplicate capability flags on `bind r
  source-file` reload, per the repo's existing tmux.conf rationale).
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
- `set -s set-clipboard on` + `set -g allow-passthrough on` (tmux 3.5+ takes
  explicit `on`/`off`/`all`; `all` additionally fires from *inactive* panes —
  relevant if a detached worker window ever needs passthrough).
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
| `prefix-o` / `M-s` | `run-shell '~/.local/bin/sesh-picker.sh'` | existing rich sesh+fzf picker (run-shell + fzf-tmux -p; respects double-popup gotcha) |
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

**Hook wiring (`dot_claude/settings.json`).** Both events use the standard hook
schema; the event payload arrives on the script's **stdin** as JSON, and the
script's **stdout** JSON is read back by Claude Code to emit the `terminalSequence`:
```json
"Notification": [
  { "matcher": "", "hooks": [
    { "type": "command", "command": "~/.local/bin/claude-tmux-notify notification" } ] }
],
"Stop": [
  { "matcher": "", "hooks": [
    { "type": "command", "command": "~/.local/bin/claude-tmux-notify stop" } ] }
]
```
`claude-tmux-notify` reads the event JSON on stdin, optionally marks the calling
window via the tmux socket (`tmux set-option -w -t "$TMUX_PANE" @needs_attention 1`),
then prints `{"terminalSequence":"<OSC-777 notify><BEL>"}` on stdout. The existing
`PreCompact`/`PreToolUse`/`PostToolUse` blocks are preserved; only `Notification`
and `Stop` are added.

**Coexist edge case:** the tmux side-effect must be guarded
(`[[ -n "$TMUX_PANE" ]] && tmux …`) because in coexist mode Claude may run under
**cmux.app**, where `$TMUX_PANE` is unset — the `tmux` call would error. The stdout
`terminalSequence` path is unaffected (no TTY/tmux dependency), so the desktop
notification still fires under cmux; only the tmux window-flag side-effect no-ops.

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
| catppuccin/tmux | tag **v2.3.0** | `.chezmoiexternal.toml` `type="archive"` (tag tarball, **immutable pin**) | `run ~/.config/tmux/plugins/catppuccin/tmux/catppuccin.tmux` |
| extrakto | **commit SHA** (no tags exist) | `.chezmoiexternal.toml` `type="archive"` (SHA tarball, **immutable pin**) | `run-shell ~/.config/tmux/plugins/extrakto/extrakto.tmux` |
| tmux-fingers | brew **tap** | `dot_Brewfile`: `tap "morantron/tmux-fingers"` + `brew "tmux-fingers"` (Crystal; formula builds via `shards`, installs **only the binary**) | `run-shell "tmux-fingers load-config"` (binary's own integration subcommand — brew ships no `.tmux` loader) |
| sesh | brew **2.26.2** | `dot_Brewfile` (formula, bottled) | n/a (CLI binary) |

- **tmux-fingers install:** Crystal project (corrected from design-review round 1,
  which assumed Rust/`cargo`). Installed via its **Homebrew tap**
  (`tap "morantron/tmux-fingers"` + `brew "tmux-fingers"` in `dot_Brewfile`); the
  formula compiles with `shards` (brew auto-installs the `crystal` dep) and installs
  **only the `tmux-fingers` binary** — no `.tmux` loader. The tmux integration is the
  binary's `load-config` subcommand, invoked from `tmux.conf` via
  `run-shell "tmux-fingers load-config"`. The existing `brew bundle` `run_onchange_`
  picks up the formula; no bespoke build script. **Gotcha:** newer Homebrew refuses
  third-party taps until trusted once —
  `brew trust --formula morantron/tmux-fingers/tmux-fingers`.
- **extrakto runtime deps:** `python3` + `fzf` (both present).
- **archive pins:** `type="archive"` (not `git-repo`) is used for catppuccin and
  extrakto so the vendored state is immutable — `git-repo` would `git pull` and
  drift on each apply, violating the reproducibility principle.
- **catppuccin v2.3.0** loaded with the v2 status-module shape (§2 gotcha #5).

Theme config (v2.3.0 shape):
```
set -g @catppuccin_flavor "macchiato"
set -g @catppuccin_window_status_style "rounded"
# NB: the -gF/E: freeze gotcha (§2 #5) applies to *_text module DEFINITIONS only
# (e.g. @catppuccin_directory_text). Appending modules in status-right via #{E:...}
# below is the correct, safe expansion point — the E modifier forces evaluation there.
run ~/.config/tmux/plugins/catppuccin/tmux/catppuccin.tmux
set -g status-left ""
# -g (replace), NOT -ag: a lone module must replace tmux's default status-right
# and stay idempotent across reloads (-ag stacks + leaves the default in place).
set -g status-right "#{E:@catppuccin_status_session}"
```

## 8. chezmoi file manifest

| Path (source) | Change |
|---|---|
| `dot_config/tmux/tmux.conf` | Rewrite from scratch per §4–7 |
| `.chezmoiexternal.toml` | Add catppuccin (v2.3.0 archive) + extrakto (SHA archive) **only** — tmux-fingers is Brewfile-tap, not vendored |
| `dot_local/bin/executable_claude-tmux-notify` | **New** — hook notify script |
| `dot_claude/settings.json` | Add `Notification` + `Stop` hook entries calling the script |
| `dot_Brewfile` | Add `tap "morantron/tmux-fingers"` + `brew "tmux-fingers"`; ensure `sesh` present |
| `dot_config/ghostty/config` | Re-enable tmux auto-attach (`command = …tmux new-session -A -s main`); confirm `desktop-notifications` not disabled |

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
4. **Attention loop:** first confirm **OSC 777 specifically** is honored by the
   `terminalSequence` allowlist — emit a test sequence
   (`printf '\x1b]777;notify;test;hello\x07'` via a one-off hook or the doc's test
   recipe) and confirm a Notification Center alert fires (fall back to OSC 9 if 777
   is rejected). Then, in a Claude window, trigger a `Notification` (permission
   prompt) → Ghostty alert appears **and** the window bell flag lights in the status
   bar; `prefix-b` jumps to it; flag clears on visit. Verify a detached worker
   window also flags without stealing focus, and that the script no-ops cleanly when
   `$TMUX_PANE` is unset (cmux coexist).
5. **Coexist:** launch cmux → still functional; launch Ghostty → auto-attaches tmux.

## 11. Open risks / validate empirically

- **extended-keys modernization** (§4.1) — try `extended-keys "always"` +
  `extended-keys-format csi-u`; fall back to the manual `S-Enter` bind if any key
  regresses.
- **`terminalSequence`**: installed Claude Code is **2.1.177**, which supports it;
  still verify empirically (emit a test sequence) rather than gating on a version
  number. Fallback if ever run on an older binary: `allow-passthrough` +
  DCS-wrap-to-`#{pane_tty}` script path (documented, second-choice).
- **tmux-fingers** installs via Homebrew tap (bottle) — no source-build/toolchain
  ordering risk; reduces to "tap reachable at `brew bundle` time."
- **extrakto SHA pin** must be refreshed deliberately (no upstream tags to track).

## 12. Maximal appendix

**Implemented post-v1 (chezmoi-6an):**
- **Discoverability menu** — shipped as a native tmux `display-menu` bound to
  `prefix+Space`, **not** the `tmux-which-key` plugin. Rationale: which-key uses git
  submodules (archive-vendoring misses them), its config dir collides with the
  vendored plugin dir (chezmoi clobber), it rebuilds via python on each start, and
  its default menu lists generic ops — tailoring it to the real binds needs a full
  custom `config.yaml` anyway. The native menu gives the same learning-loop, zero deps.
- **Worker-count status segment** — `#(~/.local/bin/claude-attention-count)` in
  status-right, counting windows with the **self-clearing** `window_bell_flag`
  (simpler + auto-clears vs a sticky cache dir). `status-interval` lowered to 5s.
  `jump-needy` extracted to `~/.local/bin/tmux-jump-needy` (shared by `prefix-b` + menu).

**Still parked:**
- `extended-keys always` + `extended-keys-format csi-u` to retire the manual
  Shift+Enter bind — riskiest item (global key-encoding change, terminal-dependent,
  upstream had regressions); the manual `S-Enter` bind is kept as the safe default.
- OSC-9;4 progress forwarding (tmux 3.6) → Ghostty progress indicator for Claude.
- Click-to-teleport notifications via a modern UNUserNotificationCenter CLI.
- Per-window git branch label (`#()` shell call) if the redraw cost is acceptable.
