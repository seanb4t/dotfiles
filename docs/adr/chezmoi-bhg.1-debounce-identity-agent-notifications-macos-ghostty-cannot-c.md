<!-- markdownlint-disable MD013 -->
<!-- adr-render: source=bd:chezmoi-bhg.1; do not edit manually; use `/adr update chezmoi-bhg.1` -->

# Debounce + identity for agent notifications (macOS Ghostty cannot coalesce)

**Date:** 2026-06-14
**Status:** Accepted
**Decision:** chezmoi-bhg.1
**Deciders:** Sean

## Context

The Claude-agent attention loop fires a Stop/Notification hook (`claude-tmux-notify`) that emits an OSC-777 desktop notification through Ghostty on macOS (Darwin 27). Grounding (Context7 `/ghostty-org/ghostty` + DeepWiki) established hard platform constraints: OSC 9 and OSC 777 carry only `{title, body}` — no identifier, no OSC 99 `i=` support — and the macOS Ghostty backend (UNUserNotificationCenter) never replaces a delivered notification by a user-supplied key. The body-as-ID coalescing trick exists only on the GTK/Linux backend. No escape sequence or CLI can remove a delivered banner. Result: notifications pile up in Notification Center, carry a generic "Claude Code" title, and cannot be triaged.

## Decision

Reduce banner noise by emitting fewer, smarter banners rather than replacing them: a 20-second per-`session:window` debounce in `claude-tmux-notify` gates the desktop banner (at most one per window per 20s), and the agent identity (`session:window` + cwd basename) plus an event-type glyph (✅ Stop / ⏳ Notification) are encoded in the OSC-777 title.

## Rationale

- macOS Ghostty's UNUserNotificationCenter integration exposes no replace/cancel API reachable from a shell hook or escape sequence — "emit fewer" is the only available lever.
- Ghostty already suppresses OSC-originated banners when the emitting surface is focused (`requireFocus=true`), so the debounce only needs to gate the background/unfocused case.
- A pure-bash tmpfile stamp is zero-dependency and coexist-safe across the tmux and non-tmux (cmux) launch paths.

## Alternatives Considered

- **Protocol coalescing / replace-in-place via OSC 99 `i=` or body-as-ID (rejected):** OSC 99 is not implemented in Ghostty; body-as-ID replacement is GTK/Linux-only. Structurally impossible on macOS.
- **External UNUserNotificationCenter notifier — terminal-notifier / alerter (rejected):** both are broken on macOS 26; building a fresh native notifier is disproportionate to scope.
- **Per-window debounce + identity title + event glyph (chosen):** sparse, non-piling behaviour within the existing OSC-777 mechanism, no new runtime dependency.

## Consequences

- Positive: pile-up eliminated with no new tooling; the title now identifies the agent for triage; native click-to-focus already routes to the emitting surface.
- Negative: events within 20s of the first are dropped from the desktop (the tmux flag still updates); delivered banners cannot be retracted.
- Neutral: stamp files accumulate in `${TMPDIR}/claude-tmux-notify/` and are not cleaned up (harmless; cleared when TMPDIR is).
