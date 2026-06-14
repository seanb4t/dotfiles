# Better, Non-Persistent Agent Notifications — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Claude-agent attention loop's macOS desktop notifications sparse, identifying, event-typed, and click-actionable instead of generic banners that pile up, while keeping the tmux window flag as the always-on auto-clearing in-terminal signal.

**Architecture:** Two self-contained bash scripts shipped via chezmoi. `claude-tmux-notify` (Claude Code Stop/Notification hook) gains agent identity in the OSC-777 title, an event-type glyph, defensive sanitization, a 20s per-window debounce on the desktop banner (the BEL/tmux-flag still fires every event), and a `@claude_attn` window label. `tmux-jump-needy` (bound to `prefix-b`) becomes an identity-aware picker: 0 needy → message, 1 → jump, ≥2 → native `display-menu` labelled from `@claude_attn`. No Claude hook-wiring change; the macOS Banner (transient) style is a manual System-Settings step the user owns.

**Tech Stack:** bash (kept 3.2-safe — no `mapfile`), `jq`, the tmux socket/CLI, Claude Code's `{terminalSequence}` hook field, Ghostty OSC-777.

**Spec:** `docs/superpowers/specs/2026-06-14-agent-notifications-better-non-persistent-design.md` (bead chezmoi-bhg).

**Model (Rule 5):** all four tasks are `model:sonnet` — mechanical bash rewrites + isolated-socket verification, no architectural judgement. `plan-to-beads` should label each child `model:sonnet`.

**⚠️ Test-safety gotcha (verified, repo memory):** NEVER touch the default tmux socket during verification — it kills the user's live sessions and closes their Ghostty window. EVERY tmux command in this plan's tests uses an isolated socket (`tmux -L cfgtest …`) and tears it down with `tmux -L cfgtest kill-server`.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `dot_local/bin/executable_claude-tmux-notify` | Stop/Notification hook → identity + glyph + debounce + conditional OSC-777 + always-BEL + `@claude_attn` | Rewrite |
| `dot_local/bin/executable_tmux-jump-needy` | `prefix-b` picker: 0/1/≥2 needy handling with native `display-menu` | Rewrite |
| `dot_config/tmux/tmux.conf` | Attention-loop comment block reflects identity/debounce/`@claude_attn` | Comment-only edit; binds unchanged |
| `docs/superpowers/plans/2026-06-14-agent-notifications-better-non-persistent.md` | This plan | Create |

`dot_claude/settings.json` is unchanged — the hook already calls `claude-tmux-notify notification` / `claude-tmux-notify stop`.

---

### Task 1: Rewrite `claude-tmux-notify` — identity, glyph, debounce, conditional banner

**Files:**

- Modify (full rewrite): `dot_local/bin/executable_claude-tmux-notify`
- Test: ad-hoc shell assertions on an isolated tmux socket (no test framework in this repo)

- [ ] **Step 1: Write the failing test**

Create a scratch test script `/tmp/t-notify.sh` (NOT committed):

```bash
#!/usr/bin/env bash
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1   # resolve relative SRC from anywhere
SRC="dot_local/bin/executable_claude-tmux-notify"
fail=0; chk(){ if eval "$2"; then echo "ok: $1"; else echo "FAIL: $1"; fail=1; fi; }

# isolated tmux server, one window
tmux -L cfgtest kill-server 2>/dev/null
tmux -L cfgtest new-session -d -s t -x 80 -y 24
pane=$(tmux -L cfgtest display-message -p -t t -F '#{pane_id}')
sock=$(tmux -L cfgtest display-message -p '#{socket_path}')
run(){ TMUX="$sock,0,0" TMUX_PANE="$pane" bash "$SRC" "$1" ; }

# clear any debounce stamp from a prior run — compute the key EXACTLY as the
# script does (capture ident first so $() strips the trailing newline, THEN tr;
# piping tmux output straight to tr would turn that newline into a stray '_').
ident0=$(tmux -L cfgtest display-message -p -t "$pane" -F '#{session_name}:#{window_index} #{b:pane_current_path}')
key=$(printf '%s' "$ident0" | tr -c 'A-Za-z0-9' '_')
rm -f "${TMPDIR:-/tmp}/claude-tmux-notify/$key"

# Match the LITERAL glyph bytes in the raw sequence. Do NOT pipe through cat -v:
# it renders the ✅/⏳ UTF-8 as "M-…", and "^[" is only the OSC opener (^[]777),
# never a glyph — so "^["-based patterns can never match a correct title.
stop_seq=$(printf '{}' | run stop | jq -r .terminalSequence)
chk "stop title carries ✅ + session:window" '[[ "$stop_seq" == *"777;notify;✅ t:0"* ]]'
chk "stop body is finished-your-move"         '[[ "$stop_seq" == *"Finished"* ]]'

# Notification fires from a DIFFERENT window (window 1) so its debounce key is
# fresh and the banner is not suppressed by the stop call above.
tmux -L cfgtest new-window -t t
pane2=$(tmux -L cfgtest display-message -p -t t -F '#{pane_id}')
notif_seq=$(printf '{"message":"Allow Bash?"}' | TMUX="$sock,0,0" TMUX_PANE="$pane2" bash "$SRC" notification | jq -r .terminalSequence)
chk "notification title carries ⏳ + t:1"     '[[ "$notif_seq" == *"777;notify;⏳ t:1"* ]]'
chk "notification body is the message"        '[[ "$notif_seq" == *"Allow Bash?"* ]]'

# debounce: a SECOND stop on window 0 within 20s → BEL only, no 777;notify
dz=$(printf '{}' | run stop | jq -r .terminalSequence)
chk "debounced second banner is BEL-only"     '[[ "$dz" != *"777;notify"* ]]'

# @claude_attn window option is set on window 0
attn=$(tmux -L cfgtest show-options -wqv -t "$pane" @claude_attn)
chk "@claude_attn set on window"              '[[ -n "$attn" ]]'

# coexist: no TMUX_PANE → still emits JSON, generic title, no tmux error
co=$(printf '{}' | env -u TMUX -u TMUX_PANE bash "$SRC" stop | jq -r .terminalSequence)
chk "coexist fallback emits generic title"    '[[ "$co" == *"777;notify;✅ Claude Code"* ]]'

tmux -L cfgtest kill-server 2>/dev/null
exit $fail
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash /tmp/t-notify.sh`
Expected: FAILs — the current script emits literal `777;notify;Claude Code;…` (no glyph/identity), has no debounce, and sets `@needs_attention` not `@claude_attn`.

- [ ] **Step 3: Write the rewrite**

Replace the entire contents of `dot_local/bin/executable_claude-tmux-notify` with:

```bash
#!/usr/bin/env bash
# claude-tmux-notify — Claude Code Notification/Stop hook.
# Emits an IDENTIFYING, event-typed, DEBOUNCED Ghostty OSC-777 desktop
# notification + a BEL (tmux window flag) via the hook's {terminalSequence}
# field (Claude Code delivers it race-free through tmux). The BEL/flag fires on
# EVERY event; the desktop banner is suppressed if one already fired for this
# session:window within DEBOUNCE_SECS, so a chatty agent lights its flag without
# spamming Notification Center (which on macOS cannot coalesce — OSC 9/777 carry
# only title+body, no replace id).
# Spec: docs/superpowers/specs/2026-06-14-agent-notifications-better-non-persistent-design.md
set -uo pipefail

DEBOUNCE_SECS=20
event="${1:-notification}"
payload="$(cat)"

# --- body + glyph by event type --------------------------------------------
if [ "$event" = "stop" ]; then
  glyph="✅"
  body="Finished — your move"
else
  glyph="⏳"
  body="$(printf '%s' "$payload" | jq -r '.message // "Needs your attention"' 2>/dev/null || echo "Needs your attention")"
fi

# --- identity (which agent), guarded for cmux-coexist (no $TMUX_PANE) -------
in_tmux=0
if [ -n "${TMUX_PANE:-}" ] && command -v tmux >/dev/null 2>&1; then
  in_tmux=1
  ident="$(tmux display-message -p -t "$TMUX_PANE" -F '#{session_name}:#{window_index} #{b:pane_current_path}' 2>/dev/null)"
  [ -z "$ident" ] && ident="Claude Code"
else
  ident="Claude Code"
fi

# --- sanitize for OSC-777 (;-delimited, BEL/ST-terminated) -----------------
# Strip newlines, then neutralise ; (field separator), BEL, ESC to spaces so a
# worktree path or model message can't split fields or terminate the sequence.
sanitize() { printf '%s' "$1" | tr -d '\n\r' | tr ';\a\033' '   '; }
title="$(sanitize "$glyph $ident")"
body="$(sanitize "$body")"

# --- mark the window for the picker (guarded) ------------------------------
# @claude_attn = glyph + short body snippet; tmux-jump-needy reads it to label
# the picker. Replaces the previously-unused @needs_attention option.
if [ "$in_tmux" = 1 ]; then
  snippet="$(printf '%s' "$body" | cut -c1-40)"
  tmux set-option -w -t "$TMUX_PANE" @claude_attn "$glyph $snippet" 2>/dev/null || true
fi

# --- debounce the desktop banner (per session:window) ----------------------
want_banner=1
if [ "$in_tmux" = 1 ]; then
  stampdir="${TMPDIR:-/tmp}/claude-tmux-notify"
  mkdir -p "$stampdir" 2>/dev/null || true
  key="$(printf '%s' "$ident" | tr -c 'A-Za-z0-9' '_')"
  stamp="$stampdir/$key"
  now="$(date +%s)"
  last="$(cat "$stamp" 2>/dev/null || echo 0)"
  if [ $(( now - last )) -lt "$DEBOUNCE_SECS" ]; then
    want_banner=0
  else
    printf '%s' "$now" > "$stamp" 2>/dev/null || true
  fi
fi

# --- build terminalSequence: BEL always; OSC-777 only when not debounced ----
bel=$'\a'
if [ "$want_banner" = 1 ]; then
  osc="$(printf '\033]777;notify;%s;%s\007' "$title" "$body")"
  seq="${osc}${bel}"
else
  seq="${bel}"
fi
jq -nc --arg seq "$seq" '{terminalSequence: $seq}'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /tmp/t-notify.sh`
Expected: all `ok:` lines, exit 0. (If the `@claude_attn` check flakes because a prior run left a debounce stamp, the test already `rm`s the stamp before the first call — re-run.)

- [ ] **Step 5: Commit**

```bash
git add dot_local/bin/executable_claude-tmux-notify
git commit -m "feat(notify): identifying, event-typed, debounced agent notifications (chezmoi-bhg)

OSC-777 title now carries the emitting agent's session:window + cwd and a
per-event glyph (✅ Stop / ⏳ Notification). A 20s per-window debounce suppresses
repeat desktop banners (the BEL/tmux flag still fires every event), and the
window is labelled with @claude_attn for the jump picker. Inputs sanitized of
;/newline/BEL/ESC. cmux-coexist (no \$TMUX_PANE) still fires a generic banner.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Rewrite `tmux-jump-needy` — identity-aware 0/1/≥2 picker

**Files:**

- Modify (full rewrite): `dot_local/bin/executable_tmux-jump-needy`
- Test: ad-hoc shell assertions on an isolated tmux socket

- [ ] **Step 1: Write the failing test**

Create `/tmp/t-jump.sh` (NOT committed):

```bash
#!/usr/bin/env bash
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1   # resolve relative SRC from anywhere
SRC="dot_local/bin/executable_tmux-jump-needy"
fail=0; chk(){ if eval "$2"; then echo "ok: $1"; else echo "FAIL: $1"; fail=1; fi; }

tmux -L cfgtest kill-server 2>/dev/null
tmux -L cfgtest new-session -d -s t -x 80 -y 24   # window 0
tmux -L cfgtest new-window -t t                    # window 1
tmux -L cfgtest new-window -t t                    # window 2
sock=$(tmux -L cfgtest display-message -p '#{socket_path}')
# JUMP_DRYRUN makes the script print its intended action to STDOUT — needed
# because the real 0-needy path uses `tmux display-message` (status bar, not
# stdout) and the 1/≥2 paths have side effects, none of which a test can read.
J(){ TMUX="$sock,0,0" JUMP_DRYRUN=1 bash "$SRC" ; }

# 0 needy: no bell flags set → message branch
out=$(J 2>&1 || true)
chk "0 needy → nothing-needs-you"          '[[ "$out" == *"nothing needs you"* ]]'

# helper: raise a bell flag on a window by writing a BEL to its pane
ring(){ tmux -L cfgtest send-keys -t "t:$1" "printf '\\a'" Enter; sleep 0.3; }

# 1 needy: ring window 1 → select-window branch names t:1
ring 1
out=$(J 2>&1 || true)
chk "1 needy → select-window of flagged win" '[[ "$out" == *"select-window -t t:1"* ]]'

# ≥2 needy: ring window 2 as well → display-menu listing both targets
ring 2
out=$(J 2>&1 || true)
chk "≥2 needy → display-menu"               '[[ "$out" == *"display-menu"* ]]'
chk "menu includes t:1 target"               '[[ "$out" == *"select-window -t \"t:1\""* ]]'
chk "menu includes t:2 target"               '[[ "$out" == *"select-window -t \"t:2\""* ]]'

tmux -L cfgtest kill-server 2>/dev/null
exit $fail
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash /tmp/t-jump.sh`
Expected: FAILs — the current script has no "nothing needs you" message, jumps to the first needy window even when ≥2 exist (no picker), and has no `JUMP_DRYRUN` hook, so the menu assertion fails.

- [ ] **Step 3: Write the rewrite**

Replace the entire contents of `dot_local/bin/executable_tmux-jump-needy` with:

```bash
#!/usr/bin/env bash
# tmux-jump-needy — go to the window(s) the Claude attention loop flagged (bell
# flag). 0 needy → friendly message; 1 → jump straight there; ≥2 → a native
# display-menu picker labelled from @claude_attn so you can see WHICH agent and
# why. Closes the last hop the macOS notification's click-to-focus can't make
# (Ghostty raises the surface; this lands the exact inner tmux window).
# Bound to prefix-b and surfaced in the prefix-Space action menu.
# Kept bash-3.2-safe (no mapfile): hook subprocess PATH is not guaranteed.
set -uo pipefail

fmt=$'#{window_bell_flag}\t#{session_name}:#{window_index}\t#{b:pane_current_path}\t#{@claude_attn}'

targets=(); dirs=(); attns=()
while IFS=$'\t' read -r flag target dir attn; do
  [ "${flag:-0}" = "1" ] || continue
  targets+=("$target"); dirs+=("$dir"); attns+=("$attn")
done < <(tmux list-windows -a -F "$fmt")

count=${#targets[@]}
dry="${JUMP_DRYRUN:-}"   # when set, print the intended action to stdout (for tests)

if [ "$count" -eq 0 ]; then
  if [ -n "$dry" ]; then echo "message: nothing needs you"
  else tmux display-message "✓ nothing needs you"; fi
  exit 0
fi

if [ "$count" -eq 1 ]; then
  if [ -n "$dry" ]; then echo "select-window -t ${targets[0]}"
  else tmux select-window -t "${targets[0]}"; fi
  exit 0
fi

# ≥2 needy → native display-menu. Accumulate (label, key, command) triples into
# a bash array and expand "${menu[@]}" — no eval/xargs — so glyph/space labels
# from @claude_attn quote safely. session:window is whitespace-free → safe target.
menu=()
i=0
while [ "$i" -lt "$count" ]; do
  prefix="${attns[$i]:-•}"
  label="$prefix ${targets[$i]}  ${dirs[$i]}"
  menu+=("$label" "" "select-window -t \"${targets[$i]}\"")
  i=$(( i + 1 ))
done

if [ -n "$dry" ]; then
  printf 'display-menu\n'
  printf '%s\n' "${menu[@]}"   # one menu element per line: label, "", command, …
  exit 0
fi

tmux display-menu -T "#[align=centre,fg=#c6a0f6,bold]  needs you " -x C -y C "${menu[@]}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /tmp/t-jump.sh`
Expected: all `ok:` lines, exit 0.

- [ ] **Step 5: Commit**

```bash
git add dot_local/bin/executable_tmux-jump-needy
git commit -m "feat(notify): identity-aware needy-window picker (chezmoi-bhg)

tmux-jump-needy now spans sessions and handles 0/1/≥2 needy windows: 0 shows a
'nothing needs you' message, 1 jumps directly (prior behaviour), ≥2 opens a
native display-menu labelled from @claude_attn so you pick the exact agent —
the last hop the desktop notification's surface-level click-to-focus can't make.
Kept bash-3.2-safe; JUMP_DRYRUN prints the menu argv for testing.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Refresh the tmux.conf Attention-loop comment block

**Files:**

- Modify: `dot_config/tmux/tmux.conf` (the `--- Attention loop ---` block, around lines 77–84). Binds and `set -g` options are UNCHANGED — comment text only.

- [ ] **Step 1: Read the current block**

Run: `rg -n -A8 'Attention loop' dot_config/tmux/tmux.conf`
Expected: the block with the `monitor-bell`/`visual-bell`/`bell-action` options and the `prefix-b` bind.

- [ ] **Step 2: Update only the comment lines**

Replace the two comment lines:

```
# Claude hook emits a BEL via terminalSequence; monitor-bell lights the window
# flag (shown by catppuccin @..._window_flags "icon"). No focus steal.
```

with:

```
# Claude hook (claude-tmux-notify) emits a BEL every event → monitor-bell lights
# the window flag (catppuccin @..._window_flags "icon"); the desktop banner is
# debounced + identity-titled separately. No focus steal. prefix-b opens an
# identity picker (tmux-jump-needy) when >1 window is flagged.
```

Leave `set -g monitor-bell on`, `set -g visual-bell off`, `set -g bell-action other`, and `bind b run-shell '~/.local/bin/tmux-jump-needy'` exactly as they are.

- [ ] **Step 3: Verify config still parses on an isolated socket**

Run:
```bash
tmux -L cfgtest kill-server 2>/dev/null
tmux -L cfgtest new-session -d -s t
tmux -L cfgtest source-file dot_config/tmux/tmux.conf 2>&1 | tee /tmp/srcout
tmux -L cfgtest list-keys 2>/dev/null | rg "bind.* b .*tmux-jump-needy" || tmux -L cfgtest list-keys | rg tmux-jump-needy
tmux -L cfgtest kill-server 2>/dev/null
```
Expected: `source-file` prints no error lines; the `prefix-b → tmux-jump-needy` bind is listed. (Plugin `run-shell` lines may warn if vendored plugins aren't present in the test server — those warnings are unrelated to this change and acceptable.)

- [ ] **Step 4: Commit**

```bash
git add dot_config/tmux/tmux.conf
git commit -m "docs(tmux): attention-loop comment reflects debounced identity notifications (chezmoi-bhg)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: End-to-end verification + chezmoi apply

**Files:** none modified — verification only.

- [ ] **Step 1: Re-run both unit test scripts**

Run: `bash /tmp/t-notify.sh && bash /tmp/t-jump.sh`
Expected: both exit 0, all `ok:` lines.

- [ ] **Step 2: Confirm chezmoi sees only the intended changes**

Run:
```bash
chezmoi diff dot_local/bin/executable_claude-tmux-notify dot_local/bin/executable_tmux-jump-needy dot_config/tmux/tmux.conf 2>&1 | head -80
```
Expected: diffs for exactly these three managed files; both scripts remain mode `0755` (executable). No diff in `dot_claude/settings.json`.

- [ ] **Step 3: Apply to the live home dir and reload tmux config**

Run:
```bash
chezmoi apply ~/.local/bin/claude-tmux-notify ~/.local/bin/tmux-jump-needy ~/.config/tmux/tmux.conf
tmux source-file ~/.config/tmux/tmux.conf   # reloads the REAL server (safe: source-file only, never kill-server)
```
Expected: files updated in `~/.local/bin` and `~/.config/tmux`; tmux reload prints no errors. (Per the gotcha: only `source-file` against the live server — never `kill-server`.)

- [ ] **Step 4: Live smoke test (manual, optional)**

In a real tmux window running Claude Code, trigger a Stop (let a turn finish) while that window is **not** focused. Expected: one macOS banner titled `✅ <session:window> <dir>`; clicking it raises the emitting Ghostty surface; the tmux window shows its bell-flag icon. A second Stop within 20s lights the flag again but fires no new banner. With two flagged windows, `prefix-b` opens the labelled `display-menu`.

- [ ] **Step 5: Clean up scratch tests**

Run: `rm -f /tmp/t-notify.sh /tmp/t-jump.sh`

---

## Out of Scope (YAGNI — from spec §8)

- Protocol coalescing / replace-in-place (impossible on macOS Ghostty).
- External `UNUserNotificationCenter` notifier (broken on macOS 26).
- `#(claude-attention-count)` status segment / dashboard window (deferred).
- macOS Banner (transient) style — user sets it in System Settings → Notifications → Ghostty (SIP-protected; not chezmoi-scriptable).

## Rollback

Revert the three managed files and `chezmoi apply` them; no state migration. `@claude_attn` is a transient per-server window option (gone on tmux restart). The debounce stamp dir `${TMPDIR}/claude-tmux-notify/` is disposable.
<!-- adr-capture: sha256=f2ce97178491f05a; session=cli; ts=2026-06-14T13:30:48Z; adrs=chezmoi-bhg.1,chezmoi-bhg.2 -->
