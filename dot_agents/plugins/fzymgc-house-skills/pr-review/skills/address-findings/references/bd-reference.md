# bd CLI Reference

Subset of `bd` commands used by the address-review-findings skill.
All commands use long flags only — no shorthand.

## bd list — Query findings

```bash
bd list --parent <epic-id> --status open --json
bd list --parent <epic-id> --status open --label "aspect:code" --json
bd list --label "pr-review,pr:<number>" --json
```

## bd create — Create work and deferred beads

```bash
bd create "<title>" \
  --type task \
  --parent <epic-id> \
  --labels "label1,label2" \
  --external-ref "<url>" \
  --deps "discovered-from:<finding-id>" \
  --description "<details>" \
  --silent
```

## bd update — Close beads, add labels

```bash
bd update <id> --status closed
bd update <id> --add-label deferred
bd update <id> --status in_progress
```

## bd dep add — Set dependencies

```bash
bd dep add <issue-id> --depends-on <dependency-id>                          # blocks (default type)
bd dep add <issue-id> --depends-on <dependency-id> --type discovered-from   # traceability
bd dep add <issue-id> --depends-on <dependency-id> --type validates         # review validates fix
bd dep add <issue-id> --depends-on <dependency-id> --type caused-by         # root cause link
```

## bd dep relate — Bidirectional link (no blocking)

```bash
bd dep relate <id1> <id2>
```

## bd dep list — Check dependencies

```bash
bd dep list <id>
```

## bd comments add — Annotate beads

```bash
bd comments add <id> "Review failed: <reason>"
bd comments add <id> --file notes.txt
```

## bd search — Find project epics

```bash
bd search "<query>" --status open --type epic --json
```
