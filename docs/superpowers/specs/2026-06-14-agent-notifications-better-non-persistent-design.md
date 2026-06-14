# Design: Better, non-persistent tmux/Ghostty agent-attention notifications

- **Bead:** chezmoi-bhg
- **Date:** 2026-06-14
- **Status:** Design — pending design-reviewer
- **Author:** Sean (with Claude Opus 4.8)
- **Builds on:** `docs/superpowers/specs/2026-06-13-ghostty-tmux-agent-cockpit-design.md` (bead chezmoi-6an), Layer 3 — the attention loop.

## 1. Context & goal

The Ghostty + tmux agent cockpit (chezmoi-6an) wired a Claude Code `Notification`/`Stop`
hook → `claude-tmux-notify` → an **OSC-777 macOS desktop notification** + a **BEL** that
lights the tmux window's bell flag. In daily use the desktop notifications are:

- **Persistent / piling up** — every `Stop` and every `Notification` event fires a fresh
  banner. They stack in Notification Center, carry the generic title `Claude Code`, and
  must be cleared by hand.
- **Unidentifiable** — you cannot tell *which* agent (which tmux session/window, which
  worktree) the banner came from, so a pile of them can't be triaged.
- **Undifferentiated** — `Stop` ("done, your move") looks identical to `Notification`
  ("needs input / permission").

Goal: make the desktop notifications **sparse, identifying, event-typed, and
click-actionable**, and shift the *persistent* part of the signal entirely onto the
in-terminal tmux flag (which auto-clears on visit). Scope is the notification
experience only; the rest of the cockpit (chezmoi-6an) is unchanged.

### What the user asked for (decisions captured 2026-06-14)

- **Not persistent** = the macOS notifications must stop piling up.
- **Better** = (a) identify which agent, (b) click-to-focus, (c) distinguish Stop vs
  needs-input.
- **Scope** = A + B (smart script **and** a precise in-terminal teleport picker).
- **Debounce** = suppress repeat desktop banners from the same window within ~20s; the
  tmux flag still updates on every event.
- **Banner style** = the user sets Ghostty notifications to transient ("temporary"/Banner)
  in System Settings themselves; this design does not script it.

## 2. Grounding & currency

Verified 2026-06-14 via Context7 (`/ghostty-org/ghostty`) and DeepWiki
(`ghostty-org/ghostty`), plus probe of the live repo. Traces recorded as `bd note`s on
chezmoi-bhg.

### Key mechanism findings (authoritative)

1. **Ghostty OSC 9 / OSC 777 carry only `{title, body}`.** The parser
   (`src/terminal/osc.zig`, `parsers/rxvt_extension.zig`) builds
   `show_desktop_notification: struct { title, body }`. There is **no identifier /
   replace field**, and **no OSC 99 (`i=`) support**. (Context7.)
2. **macOS Ghostty does NOT coalesce notifications.** The body-as-ID replacement trick
   exists **only on the GTK/Linux backend** (`gio.Notification` keyed by body). The
   macOS backend uses `UNUserNotificationCenter`; it tracks delivered notifications in a
   `notificationIdentifiers` set but never replaces by a user-supplied id. **Conclusion:
   protocol-level coalescing is impossible on macOS today**, and nothing but Ghostty
   itself can remove a delivered notification (no escape sequence, no CLI). (DeepWiki.)
3. **Click-to-focus is native on macOS and already works.** `handleUserNotification`
   (`SurfaceView_AppKit.swift`) runs `makeKeyAndOrderFront` + `Ghostty.moveFocus(to:)` to
   the **exact surface that emitted the notification**. The current script simply does
   not exploit it. It cannot reach an inner tmux window — Ghostty has no knowledge of
   tmux's window list — so the last hop (surface → inner tmux window) is the picker's job
   (Component 2). (DeepWiki.)
4. **`requireFocus=true` is the free pile-up gate.** For **OSC-originated**
   notifications (our path — the OSC-777 `notify` escape sequence) Ghostty sets
   `requireFocus=true`, so a banner is **suppressed when its surface is already
   focused**. The remaining noise is purely from background/unfocused agents — exactly
   where a banner is wanted, but only *once*, which motivates the debounce. (DeepWiki.)
   Note: Ghostty's *internal* `notify-on-command-finish` feature uses
   `requireFocus=false` (always fires); that is a **different** code path we do not use,
   so its always-fire behaviour does not apply here.

### Consequences for the design

- "Not persistent" **cannot** be achieved by replacing/clearing notifications. It must be
  achieved by **emitting fewer, smarter** ones: identity in the title, per-event-type
  framing, and a per-window debounce. The transient ("Banner") presentation is a macOS
  System-Settings choice the user owns.
- The **two surfaces get opposite persistence**, by design:

  | Surface | Role | Persistence |
  |---|---|---|
  | tmux window bell flag (in-terminal) | "which window needs me" | persistent-until-visited; auto-clears on visit; updates on **every** event |
  | macOS desktop banner (OSC-777) | walk-away interrupt | sparse; debounced; identifying; click-to-focus; transient (Banner style) |

## 3. Design principles

1. **Keep the cheap signal cheap.** The tmux flag is the always-on, zero-noise,
   auto-clearing indicator. It fires on every event.
2. **Make the expensive signal rare and actionable.** A desktop banner only when it adds
   value (background agent, not just-fired), and when it appears it identifies the agent
   and is click-to-focus.
3. **No new runtime dependencies.** Pure bash + the tmux socket + Claude Code's
   `terminalSequence` field. No external notifier (terminal-notifier/alerter are broken
   on macOS 26 per verified memory; Darwin 27 here).
4. **Coexist-safe.** All tmux side-effects guarded on `$TMUX_PANE`; under cmux.app the
   desktop banner still fires (stdout path is TTY-independent), the tmux bits no-op.
5. **chezmoi-native.** Scripts ship as managed `executable_*` files; no interactive
   bootstrap.

## 4. Component 1 — `claude-tmux-notify` rewrite

Path: `dot_local/bin/executable_claude-tmux-notify` (→ `~/.local/bin/claude-tmux-notify`).
Invoked by the existing `Notification` and `Stop` hooks (wiring in
`dot_claude/settings.json` is **unchanged**).

Behaviour, in order:

1. **Read event + payload.** `event="${1:-notification}"`; `payload="$(cat)"`; extract
   `body` — for `stop` a fixed "Finished — your move", for `notification`
   `jq -r '.message // "Needs your attention"'`.
2. **Resolve identity (guarded).** If `$TMUX_PANE` set and `tmux` present:
   `ident="$(tmux display-message -p -t "$TMUX_PANE" -F '#{session_name}:#{window_index} #{b:pane_current_path}')"`.
   Else `ident="Claude Code"` (coexist / non-tmux fallback).
3. **Compose title + glyph by event type.** `stop` → glyph `✅`, `notification` → glyph
   `⏳`. `title="<glyph> <ident>"`. **Sanitize** `title` and `body` of `;`, **newlines**,
   and control bytes — OSC-777 is `;`-delimited and BEL/ST-terminated, so a `;` splits
   fields and a `\n`/BEL/ESC could terminate the sequence early. Concretely:
   `tr -d '\n\r' | tr ';\a\033' '   '`.
4. **Mark the window for the picker (guarded).** When `$TMUX_PANE` set:
   `tmux set-option -w -t "$TMUX_PANE" @claude_attn "<glyph> <body-snippet>"`
   (`<body-snippet>` = first ~40 chars of body). This replaces the currently-unused
   `@needs_attention` option. Component 2 reads `@claude_attn` to label the picker.
5. **Debounce the desktop banner (20s, per session:window).**
   - Stamp dir: `dir="${TMPDIR:-/tmp}/claude-tmux-notify"`; `mkdir -p "$dir"`.
   - Stamp key: the `ident` with unsafe chars replaced (`tr -c 'A-Za-z0-9' _`); file
     `"$dir/$key"` holds the epoch seconds of the last desktop banner.
   - `now=$(date +%s)`; `last=$(cat "$dir/$key" 2>/dev/null || echo 0)`.
   - `want_banner=1` if `(now - last) >= 20`, else `0`. When `want_banner=1`, write
     `now` to the stamp file.
   - When `$TMUX_PANE` is unset (coexist), skip debounce bookkeeping and always set
     `want_banner=1` (no stable per-window key available).
6. **Build the terminal sequence.**
   - BEL always: `bel=$'\a'` (lights the tmux flag every event).
   - If `want_banner=1`: `osc="$(printf '\033]777;notify;%s;%s\007' "$title" "$body")"`;
     `seq="${osc}${bel}"`. Else `seq="${bel}"`.
   - Emit `jq -nc --arg seq "$seq" '{terminalSequence: $seq}'`.

Net effect: the tmux flag updates on **every** event; the macOS banner appears at most
once per 20s per window, is titled with the agent's `session:window dir`, is glyph-typed
by event, and click-focuses its emitting Ghostty surface natively.

### Edge cases

- **No tmux (cmux coexist):** identity falls back to `Claude Code`, no flag/option writes,
  banner always fires (no debounce key) — same desktop UX as before, just generic title.
- **OSC-777 injection:** titles/bodies are sanitized of `;`, newlines, BEL, ESC so a worktree path
  or model message can't break the sequence or smuggle control bytes (the Claude Code
  allowlist already restricts emittable OSCs, but the script sanitizes defensively).
- **Stamp dir on a multi-user box:** `${TMPDIR}` is per-user on macOS, so keys don't
  collide across users.

## 5. Component 2 — `tmux-jump-needy` → identity picker

Path: `dot_local/bin/executable_tmux-jump-needy` (→ `~/.local/bin/tmux-jump-needy`).
Bound to `prefix-b` and surfaced in the `prefix-Space` action menu (existing binds in
`dot_config/tmux/tmux.conf`; no bind change required).

Algorithm:

1. Collect needy windows: `tmux list-windows -a -F '#{window_bell_flag}\t#{session_name}:#{window_index}\t#{b:pane_current_path}\t#{@claude_attn}'`
   filtered to `window_bell_flag == 1`. (`-a` so it spans sessions; the cockpit runs
   grouped sessions.)
2. **0 needy** → `tmux display-message "✓ nothing needs you"`.
3. **1 needy** → `tmux select-window -t <session:window>` directly (preserves today's
   one-keystroke behaviour).
4. **≥2 needy** → build a native `tmux display-menu` titled "  needs you ", one row per
   needy window: label `"<label-prefix> <session:window>  <dir>"`, action
   `select-window -t <session:window>`. **`<label-prefix>`** = `@claude_attn` when set,
   else a neutral `•` (a window can carry a bell flag without ever having run
   `claude-tmux-notify` — e.g. a pre-existing session or a manual bell — so
   `#{@claude_attn}` may expand empty; the `•` fallback keeps the row aligned).
   Native menu = keyboard-native, no fzf, honours the repo's "never `display-popup`
   wrapping `fzf-tmux -p`" double-popup gotcha.
5. Visiting any window clears its bell flag natively; `@claude_attn` is harmless if stale
   (overwritten on the next event).

`display-menu` is built by **accumulating the positional `(label, key, command)` triples
into a bash array** (`menu+=("$label" "" "select-window -t $target")`) and expanding it
`"${menu[@]}"` into one `tmux display-menu ...` call — not via `eval`/`xargs` — so labels
that contain spaces/glyphs (from `@claude_attn`) are quoted safely. `session:window` is
whitespace-free, so it is a safe menu target; an empty `""` menu key gives each row an
auto-assigned mnemonic.

## 6. Component 3 — macOS Banner (transient) presentation

The transient-vs-persistent behaviour (Banners auto-dismiss; Alerts persist until
dismissed) is **System Settings → Notifications → Ghostty → Banners**. It lives in a
SIP-protected prefs store (`com.apple.ncprefs`) that cannot be reliably `defaults`-written
and needs a re-login to take effect, so it is **not** chezmoi-scripted. The user sets it
manually (already done / will do). Documented here as the one external step that completes
the "not persistent" goal: debounce + identity reduce *how many* banners appear; Banner
style controls *how long each lingers*.

## 7. Files touched

| File | Change |
|---|---|
| `dot_local/bin/executable_claude-tmux-notify` | Rewrite: identity + event-typed title, `@claude_attn` window label, 20s per-window debounce, conditional OSC-777, always-BEL |
| `dot_local/bin/executable_tmux-jump-needy` | Upgrade: 0/1/≥2 needy handling, native `display-menu` identity picker spanning sessions |
| `dot_config/tmux/tmux.conf` | Comment-only refresh of the Attention-loop block if wording drifts; binds unchanged |
| `docs/superpowers/specs/2026-06-14-agent-notifications-better-non-persistent-design.md` | This spec |

`dot_claude/settings.json` hook wiring is **unchanged**.

## 8. Out of scope (YAGNI)

- **Protocol coalescing / replace-in-place** — impossible on macOS Ghostty (finding §2.2).
- **External `UNUserNotificationCenter` notifier** for real identifiers — only available
  tools are broken on macOS 26 (verified memory); disproportionate to build fresh.
- **`#(claude-attention-count)` status segment / dashboard window** — deferred; the flag +
  picker cover the need. Re-open if a persistent count is wanted later.
- **Per-event-type sound** — OSC-777 carries no sound field; differentiation is glyph/text
  only.

## 9. Testing & verification

Per the repo's verified gotcha, **never** touch the default tmux socket during testing —
it would kill Sean's live sessions and close the Ghostty window. Use an isolated socket.

1. **Identity + event title (unit, no real notification):** run the script with a faked
   `$TMUX_PANE` on an isolated server and stubbed stdin, assert the emitted
   `terminalSequence` JSON contains `777;notify;✅ <sess:win> <dir>;...` for `stop` and the
   `⏳` glyph + `.message` body for `notification`.
   ```bash
   tmux -L cfgtest new-session -d -s t
   pane=$(tmux -L cfgtest display-message -p -t t -F '#{pane_id}')
   TMUX=$(tmux -L cfgtest display-message -p '#{socket_path}') TMUX_PANE=$pane \
     bash dot_local/bin/executable_claude-tmux-notify stop </dev/null | jq -r .terminalSequence | cat -v
   ```
2. **Debounce:** invoke twice within 20s → second emission's `terminalSequence` is BEL-only
   (no `777;notify`). Invoke after >20s (or clear the stamp) → banner returns.
3. **Picker branches:** with 0/1/2 bell-flagged windows on the isolated server, confirm the
   "nothing needs you" message / direct select / `display-menu` respectively
   (`tmux -L cfgtest list-windows`, set bell flags via `select-window` + a `printf '\a'`
   into a pane, or assert the menu argv the script builds).
4. **Coexist fallback:** run with `TMUX_PANE` unset → JSON still emitted, title
   `Claude Code`, no tmux errors.
5. **chezmoi:** `chezmoi diff dot_local/bin/...` shows only intended changes; both scripts
   land executable.
6. Tear down: `tmux -L cfgtest kill-server`.

## 10. Rollback

Both scripts are self-contained; reverting the two files restores the prior behaviour.
No state migration, no plugin or hook-wiring change. The `@claude_attn` window option is
transient (per-server, lost on tmux restart).
