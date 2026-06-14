<!-- markdownlint-disable MD013 -->
<!-- adr-render: source=bd:chezmoi-bhg.2; do not edit manually; use `/adr update chezmoi-bhg.2` -->

# Split agent-notification persistence across tmux flag and desktop banner

**Date:** 2026-06-14
**Status:** Accepted
**Decision:** chezmoi-bhg.2
**Deciders:** Sean

## Context

The hook previously fired both a BEL (tmux bell flag) and an OSC-777 desktop banner on every Stop/Notification event. The two signals have different natural persistence and different audiences: the tmux bell flag is in-terminal and auto-clears when the window is visited; the desktop banner is a walk-away interrupt that does not auto-clear and stacks in Notification Center. Treating them identically caused both under-signalling (no durable in-terminal indicator) and over-signalling (banner pile-up).

## Decision

Give the two surfaces opposite persistence. Emit BEL on every event (updating the tmux window bell flag — the persistent, auto-clearing "which window needs me" indicator), and emit the OSC-777 desktop banner only when the 20s debounce gate passes (the sparse, transient walk-away interrupt). A `@claude_attn` window option carries the last event snippet so the `prefix-b` picker can label needy windows.

## Rationale

- tmux window bell flags auto-clear on visit — persistence-until-attended is native and free.
- OSC-originated Ghostty banners suppress themselves when the surface is focused (`requireFocus=true`), making them structurally suited to the background-interrupt role.
- The two surfaces have complementary persistence models that cannot be collapsed into one without losing a property (durable triage indicator OR transient interrupt).

## Alternatives Considered

- **Only the OSC-777 desktop banner, drop the tmux flag (rejected):** banners are transient and missable; nothing durable remains to show which window needs attention.
- **Only the tmux bell flag, drop the desktop banner (rejected):** zero desktop noise, but no walk-away interrupt — the operator must actively poll windows.
- **Dual signal with opposite persistence (chosen):** each surface does what it is structurally best at.

## Consequences

- Positive: the in-terminal cockpit always reflects current attention state with no manual upkeep; desktop banner volume tracks time-away, not event volume.
- Negative: the persistent-vs-transient banner style (Alert vs Banner) is not chezmoi-scriptable — it lives in SIP-protected `com.apple.ncprefs`, so the user sets it manually in System Settings.
- Neutral: the `@claude_attn` window option is overwritten each event and is transient (lost on tmux server restart) — intentionally so.
