# Ghostty + tmux Agent Cockpit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the cmux.app daily driver with a from-scratch, keyboard-native Ghostty + tmux config (cmux kept installed for coexist), centered on a Claude-Code-hook → Ghostty-OSC-777 + tmux-bell attention loop.

**Architecture:** A rewritten `tmux.conf` (mouse-off, native OSC-52 clipboard, sesh/choose-tree switching, catppuccin v2.3.0) loads three vendored/brewed plugins. A `claude-tmux-notify` hook script emits `{terminalSequence}` JSON that Claude Code delivers to Ghostty as an OSC-777 desktop notification plus a BEL that lights the tmux window flag. Ghostty is re-pointed to auto-attach tmux; cmux.app is untouched.

**Tech Stack:** tmux 3.6b, Ghostty (libghostty), chezmoi (`type="archive"` externals + Brewfile), Homebrew tap `morantron/tmux-fingers` (Crystal), `extrakto` (Python+fzf), `catppuccin/tmux` v2.3.0, `sesh`, Claude Code hooks (`terminalSequence`, binary 2.1.177).

**Spec:** `docs/superpowers/specs/2026-06-13-ghostty-tmux-agent-cockpit-design.md` · **Bead:** chezmoi-6an

> **Testing note (dotfiles adaptation):** there is no unit-test harness for a tmux config. Each task's "test" is a concrete **verification command with expected output** run against a live tmux server / the applied dotfile — the config analog of red/green. Apply scoped (`chezmoi apply <path>`) to avoid unrelated `run_onchange_` scripts. Commit after each green task.

---

## File Structure

| File | Responsibility |
|---|---|
| `dot_Brewfile` | Adds `tap "morantron/tmux-fingers"`, `brew "tmux-fingers"`, `brew "sesh"` |
| `.chezmoiexternal.toml` | Immutable `type="archive"` pins for catppuccin v2.3.0 + extrakto @ SHA |
| `dot_config/tmux/tmux.conf` | The whole config: base, clipboard, switching, theme, attention binds, plugin loads |
| `dot_local/bin/executable_claude-tmux-notify` | Hook script: stdin event JSON → tmux flag + `{terminalSequence}` stdout |
| `dot_claude/settings.json` | Adds `Notification` + `Stop` hook entries (preserves existing blocks) |
| `dot_config/ghostty/config` | Re-enables tmux auto-attach (coexist switch) |

---

### Task 1: Acquire plugins (Brewfile tap + chezmoi archive externals)

**Files:**
- Modify: `dot_Brewfile`
- Modify: `.chezmoiexternal.toml`

- [ ] **Step 1: Add the tap + brews to `dot_Brewfile`**

Add `tap "morantron/tmux-fingers"` into the alphabetical tap block (between `tap "jbangdev/tap"` and `tap "nats-io/nats-tools"`):

```ruby
tap "morantron/tmux-fingers"
```

Add `tmux-fingers` into the alphabetical `brew` block near other `t*` brews. (`brew "sesh"` is **already present** at `dot_Brewfile:166` — leave it as-is.)

```ruby
brew "tmux-fingers"
```

- [ ] **Step 2: Add the archive externals to `.chezmoiexternal.toml`**

Append (immutable pins — `refreshPeriod` is long because the URLs are version/SHA-locked):

```toml
[".config/tmux/plugins/catppuccin/tmux"]
  type = "archive"
  url = "https://github.com/catppuccin/tmux/archive/refs/tags/v2.3.0.tar.gz"
  stripComponents = 1
  refreshPeriod = "8760h"

[".config/tmux/plugins/extrakto"]
  type = "archive"
  url = "https://github.com/laktak/extrakto/archive/d1af77988081dae496fa4a1f5e5e6bc9ef66767f.tar.gz"
  stripComponents = 1
  refreshPeriod = "8760h"
```

- [ ] **Step 3: Install the brews (tap + bottle)**

Run:
```bash
brew tap morantron/tmux-fingers && brew install tmux-fingers sesh
```
Expected: both install; `tmux-fingers` pulls a bottle (no Crystal/`shards` build).

- [ ] **Step 4: Materialize the archive externals**

Run:
```bash
chezmoi apply ~/.config/tmux/plugins
```
Expected: no error; chezmoi downloads + extracts both archives.

- [ ] **Step 5: Verify plugin files exist on disk**

Run:
```bash
ls ~/.config/tmux/plugins/catppuccin/tmux/catppuccin.tmux \
   ~/.config/tmux/plugins/extrakto/extrakto.tmux
```
Expected: both paths printed (no "No such file").

- [ ] **Step 6: Confirm the tmux-fingers binary + integration command**

Run:
```bash
command -v tmux-fingers && tmux-fingers version
```
Expected: the binary resolves and prints `2.7.1`. NOTE: the Homebrew bottle ships **only the binary** (no `tmux-fingers.tmux` loader). The tmux integration is the binary's own `load-config` subcommand — Task 2's conf uses `run-shell "tmux-fingers load-config"` (binds `@fingers-key`, default `prefix-F`), which also skips the repo wrapper's self-update wizard.

- [ ] **Step 7: Commit**

```bash
git add dot_Brewfile .chezmoiexternal.toml
git commit -m "feat(tmux): vendor catppuccin/extrakto (archive) + tmux-fingers/sesh (brew) (chezmoi-6an)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Write `tmux.conf` from scratch

**Files:**
- Modify (full replace): `dot_config/tmux/tmux.conf`

- [ ] **Step 1: Replace the file with the complete config**

Write `dot_config/tmux/tmux.conf` with exactly this content (the tmux-fingers line uses the binary's own `load-config` subcommand — the brew bottle ships no `.tmux` loader):

```tmux
# =============================================================================
# tmux — Ghostty keyboard-native agent cockpit (chezmoi-6an)
# Vendored plugins via chezmoiexternal + Homebrew (no TPM). Spec:
# docs/superpowers/specs/2026-06-13-ghostty-tmux-agent-cockpit-design.md
# =============================================================================

# PATH for homebrew (vendored plugin run-shell + tools)
set-environment -g PATH "/opt/homebrew/bin:/usr/local/bin:/bin:/usr/bin"

# --- Base -------------------------------------------------------------------
unbind C-b
set -g prefix C-Space
bind C-Space send-prefix

set -g base-index 1
setw -g pane-base-index 1
set -g renumber-windows on
set -g history-limit 50000
set -sg escape-time 0
set -g focus-events on
set -g default-terminal "tmux-256color"
# indexed form (not -as) avoids stacking duplicate caps on source-file reload
set -s terminal-features[1] "xterm-256color:RGB"

# Mouse OFF — Ghostty owns the mouse (no mouse reporting). prefix-m toggles live.
set -g mouse off
bind m set -g mouse \; display "mouse #{?mouse,on,off}"

# Shift+Enter -> CSI-u for Claude Code
bind -n S-Enter send-keys Escape "[13;2u"

# Reload
bind r source-file ~/.config/tmux/tmux.conf \; display "tmux reloaded"

# --- Clipboard (native OSC-52; SSH-portable) --------------------------------
set -s set-clipboard on
set -g allow-passthrough on
setw -g mode-keys vi
bind -T copy-mode-vi v send -X begin-selection
bind -T copy-mode-vi y send -X copy-selection-and-cancel

# --- Splits / panes ---------------------------------------------------------
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
unbind '"'
unbind %
bind c new-window -c "#{pane_current_path}"
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Native directional pane nav (replaces vim-tmux-navigator)
bind -n M-h select-pane -L
bind -n M-j select-pane -D
bind -n M-k select-pane -U
bind -n M-l select-pane -R

# --- Window / session switching --------------------------------------------
bind -n M-1 select-window -t 1
bind -n M-2 select-window -t 2
bind -n M-3 select-window -t 3
bind -n M-4 select-window -t 4
bind -n M-5 select-window -t 5
bind -n M-6 select-window -t 6
bind -n M-7 select-window -t 7
bind -n M-8 select-window -t 8
bind -n M-9 select-window -t 9
bind -n M-Tab last-window
bind -n M-[ previous-window
bind -n M-] next-window
bind w choose-tree -Zw
bind o run-shell '~/.local/bin/sesh-picker.sh'
bind -n M-s run-shell '~/.local/bin/sesh-picker.sh'
bind N command-prompt -p "New session:" "new-session -s '%%'"

# --- Attention loop ---------------------------------------------------------
# Claude hook emits a BEL via terminalSequence; monitor-bell lights the window
# flag (shown by catppuccin @..._window_flags "icon"). No focus steal.
set -g monitor-bell on
set -g visual-bell off
set -g bell-action other
# prefix-b: jump to the next window awaiting attention (bell flag set)
bind b run-shell "tmux list-windows -F '#{window_bell_flag} #{window_index}' | awk '\$1==1{print \$2; exit}' | xargs -r -I{} tmux select-window -t {}"

# --- Theme (catppuccin v2.3.0) ----------------------------------------------
set -g status-left-length 100
set -g status-right-length 100
set -g @catppuccin_flavor "macchiato"
set -g @catppuccin_window_status_style "rounded"
# Window labels: index + cwd basename. Set PLAIN (set -g, not -gF) so the
# #{b:pane_current_path} value is NOT force-expanded at definition (freeze gotcha).
set -g @catppuccin_window_number "#I"
set -g @catppuccin_window_text " #{b:pane_current_path}"
set -g @catppuccin_window_current_text " #{b:pane_current_path}"
set -g @catppuccin_window_flags "icon"
run ~/.config/tmux/plugins/catppuccin/tmux/catppuccin.tmux
set -g status-left ""
set -ag status-right "#{E:@catppuccin_status_session}"

# --- Plugins (load LAST) ----------------------------------------------------
# extrakto: vendored repo (Python + fzf)
run-shell ~/.config/tmux/plugins/extrakto/extrakto.tmux
# tmux-fingers: brew ships ONLY the binary (no .tmux loader); `load-config` is
# the integration (binds @fingers-key, default prefix-F).
run-shell "tmux-fingers load-config"
```

- [ ] **Step 2: Apply the config**

Run:
```bash
chezmoi apply ~/.config/tmux/tmux.conf
```
Expected: no error.

- [ ] **Step 3: Load it on a fresh test server**

Run:
```bash
tmux kill-server 2>/dev/null; tmux new-session -d -s cfgtest \; source-file ~/.config/tmux/tmux.conf
```
Expected: no error printed (a config syntax error would print here).

- [ ] **Step 4: Verify base options**

Run:
```bash
tmux show -g prefix; tmux show -g mouse; tmux show -gw -t cfgtest:1 mode-keys
```
Expected: `prefix C-Space`, `mouse off`, `mode-keys vi`.

- [ ] **Step 5: Verify truecolor + plugins + theme**

Run:
```bash
tmux list-keys | rg -i 'fingers|extrakto' | head; tmux show -g @catppuccin_flavor
```
Expected: at least one `tmux-fingers` and one `extrakto` binding listed; `@catppuccin_flavor macchiato`. (Visually, the test session's status bar renders Catppuccin macchiato with no literal `#{...}` text — confirming no frozen module.)

- [ ] **Step 6: Verify the attention jump bind exists**

Run:
```bash
tmux list-keys | rg 'prefix.*\bb\b|select-window' | rg -i bell -A0 || tmux list-keys | rg ' b .*list-windows'
```
Expected: the `prefix b` → `run-shell ... list-windows ... window_bell_flag` binding is present.

- [ ] **Step 7: Tear down the test server + commit**

```bash
tmux kill-server 2>/dev/null
git add dot_config/tmux/tmux.conf
git commit -m "feat(tmux): from-scratch keyboard-native config (C-Space, mouse-off, OSC-52, sesh, catppuccin v2.3.0) (chezmoi-6an)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: The attention notify script

**Files:**
- Create: `dot_local/bin/executable_claude-tmux-notify`

- [ ] **Step 1: Write the script**

Create `dot_local/bin/executable_claude-tmux-notify` with exactly:

```bash
#!/usr/bin/env bash
# claude-tmux-notify — Claude Code Notification/Stop hook.
# Emits a Ghostty OSC-777 desktop notification + a BEL (tmux window flag) via
# the hook's {terminalSequence} field (Claude Code delivers it race-free through
# tmux). Spec: docs/superpowers/specs/2026-06-13-ghostty-tmux-agent-cockpit-design.md
set -uo pipefail

event="${1:-notification}"
payload="$(cat)"

if [ "$event" = "stop" ]; then
  body="Claude finished — your move"
else
  body="$(printf '%s' "$payload" | jq -r '.message // "Needs your attention"' 2>/dev/null || echo "Needs your attention")"
fi

# Optional tmux side-effect: flag the calling window. Guarded for the cmux
# coexist case where Claude runs outside tmux ($TMUX_PANE unset).
if [ -n "${TMUX_PANE:-}" ] && command -v tmux >/dev/null 2>&1; then
  tmux set-option -w -t "$TMUX_PANE" @needs_attention 1 2>/dev/null || true
fi

# OSC-777 notify (BEL-terminated) + a standalone BEL so tmux monitor-bell flags
# the window. jq encodes the control bytes (ESC, BEL) as JSON escapes.
seq="$(printf '\033]777;notify;Claude Code;%s\007\007' "$body")"
jq -nc --arg seq "$seq" '{terminalSequence: $seq}'
```

- [ ] **Step 2: Apply (chezmoi sets the executable bit from the `executable_` prefix)**

Run:
```bash
chezmoi apply ~/.local/bin/claude-tmux-notify && test -x ~/.local/bin/claude-tmux-notify && echo OK
```
Expected: `OK`.

- [ ] **Step 3: Verify it emits valid `terminalSequence` JSON containing OSC-777**

Run:
```bash
echo '{"message":"perm needed"}' | ~/.local/bin/claude-tmux-notify notification | jq -r '.terminalSequence' | cat -v
```
Expected: a line like `^[]777;notify;Claude Code;perm needed^G^G` (`^[`=ESC, `^G`=BEL).

- [ ] **Step 4: Verify the stop event + the coexist guard (no `$TMUX_PANE`)**

Run:
```bash
echo '{}' | env -u TMUX_PANE ~/.local/bin/claude-tmux-notify stop | jq -e '.terminalSequence | test("Claude finished")' && echo GUARD_OK
```
Expected: `true` then `GUARD_OK` — proves the stop body fires and the script does NOT error when `$TMUX_PANE` is unset (cmux coexist).

- [ ] **Step 5: Commit**

```bash
git add dot_local/bin/executable_claude-tmux-notify
git commit -m "feat(tmux): claude-tmux-notify hook script (OSC-777 + tmux bell flag) (chezmoi-6an)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Wire the Claude Code hooks

**Files:**
- Modify: `dot_claude/settings.json` (the `hooks` object, ~line 140)

- [ ] **Step 1: Add `Notification` + `Stop` to the hooks block**

In `dot_claude/settings.json`, replace the existing `hooks` object so it reads (preserving `PostToolUse`/`PreCompact`/`PreToolUse` exactly, adding the two new keys):

```json
  "hooks": {
    "Notification": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "~/.local/bin/claude-tmux-notify notification" } ] }
    ],
    "Stop": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "~/.local/bin/claude-tmux-notify stop" } ] }
    ],
    "PostToolUse": [
      { "matcher": "*", "hooks": [] }
    ],
    "PreCompact": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "bd prime" } ] }
    ],
    "PreToolUse": [
      { "matcher": "*", "hooks": [] }
    ]
  },
```

- [ ] **Step 2: Apply + validate JSON**

Run:
```bash
chezmoi apply ~/.claude/settings.json && jq -e '.hooks.Notification[0].hooks[0].command, .hooks.Stop[0].hooks[0].command' ~/.claude/settings.json
```
Expected: the two `claude-tmux-notify …` command strings print; non-zero exit only on malformed JSON.

- [ ] **Step 3: Empirically verify OSC-777 raises a Ghostty notification (do this in a Ghostty+tmux pane, not cmux)**

Run:
```bash
printf '\033]777;notify;test;hello from tmux\007'
```
Expected: a macOS Notification Center alert "hello from tmux". **If nothing appears**, OSC-777 may not be in your build's allowlist — fall back to OSC 9 and use it in the script instead:
```bash
printf '\033]9;hello from tmux\007'
```
Record which fired; if OSC-9 is the working one, change the script's `seq=` line to `printf '\033]9;%s\007\007' "$body"`.

- [ ] **Step 4: Commit**

```bash
git add dot_claude/settings.json
git commit -m "feat(tmux): wire Claude Notification/Stop hooks to claude-tmux-notify (chezmoi-6an)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Re-point Ghostty to tmux (coexist switch)

**Files:**
- Modify: `dot_config/ghostty/config:38-39`

- [ ] **Step 1: Re-enable the tmux auto-attach**

In `dot_config/ghostty/config`, replace the two commented lines:

```
# tmux auto-attach removed — using cmux as multiplexer
# command = /opt/homebrew/bin/tmux new-session -A -s main
```

with:

```
# Ghostty.app auto-attaches tmux (coexist: cmux.app manages its own surfaces and ignores this)
command = /opt/homebrew/bin/tmux new-session -A -s main
```

- [ ] **Step 2: Apply**

Run:
```bash
chezmoi apply ~/.config/ghostty/config && rg -n '^command = ' ~/.config/ghostty/config
```
Expected: the active (uncommented) `command = …tmux new-session -A -s main` line prints.

- [ ] **Step 3: Verify a new Ghostty window lands in tmux; cmux unaffected**

Manual: open a **new Ghostty window** → it attaches the `main` tmux session (Catppuccin status bar visible). In that window:
```bash
echo "TMUX=$TMUX"
```
Expected: non-empty `$TMUX`. Then launch **cmux.app** separately → it still opens normally (it does not read the ghostty `command` directive).

- [ ] **Step 4: Commit**

```bash
git add dot_config/ghostty/config
git commit -m "feat(ghostty): re-enable tmux auto-attach (coexist with cmux) (chezmoi-6an)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: End-to-end validation

**Files:** none (validation + final notes)

- [ ] **Step 1: Clean dry-run of the whole repo**

Run:
```bash
chezmoi apply --dry-run 2>&1 | rg -i 'error|warn' || echo "CLEAN"
```
Expected: `CLEAN` (or only unrelated, pre-existing diffs you recognize).

- [ ] **Step 2: Attention loop, end to end (Ghostty + tmux + Claude)**

Manual: in a Ghostty→tmux window, start `claude`, trigger a permission prompt (any tool needing approval). Expected: (a) a macOS Notification Center alert fires; (b) that window's Catppuccin status segment shows the **bell icon** (`󰂞`). From another window, `prefix-b` jumps to the flagged window; the flag clears on arrival.

- [ ] **Step 3: Detached-worker flag without focus steal**

Run (simulates a `/drain` worker window):
```bash
pane=$(tmux new-window -d -P -F '#{pane_id}'); tmux send-keys -t "$pane" "printf '\007'" Enter; tmux list-windows -F '#{window_index} bell=#{window_bell_flag}'
```
Expected: the new window shows `bell=1` while your focus stays put; visiting it clears the flag.

- [ ] **Step 4: Copy tiers (keyboard-native)**

Manual: (a) `prefix-[`, `/`-search, `v`, `y` → text lands on the macOS clipboard (`pbpaste`); (b) `prefix-F` shows tmux-fingers hint labels → a letter copies a token; (c) `prefix-Tab` opens extrakto → fuzzy-filter + Enter copies/inserts.

- [ ] **Step 5: Coexist guard under cmux**

Manual: in **cmux.app** (where `$TMUX_PANE` is unset), run:
```bash
echo '{"message":"x"}' | ~/.local/bin/claude-tmux-notify notification >/dev/null && echo "NO_ERROR"
```
Expected: `NO_ERROR` (script no-ops the tmux side-effect cleanly; the stdout path is unused outside Claude).

- [ ] **Step 6: Final bead notes**

```bash
bd note chezmoi-6an "Implementation complete: tmux.conf rewrite, claude-tmux-notify, archive externals (catppuccin v2.3.0 + extrakto SHA), brew tap tmux-fingers + sesh, Claude Notification/Stop hooks, ghostty tmux re-point. Verified per plan §6."
```

---

## Rollback

cmux.app and `~/.config/cmux/` are untouched throughout. To revert: comment the `command = …tmux…` line in `dot_config/ghostty/config` (`chezmoi apply`), and launch cmux.app instead of Ghostty.app. The tmux config, externals, and hook script are inert when not launched into tmux.
