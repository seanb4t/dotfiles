---
upstream_repo: obra/superpowers
upstream_version: v5.0.7
synced_at: 2026-04-01
---

# Upstream Manifest

Tracks the upstream `obra/superpowers` version and per-file modification status
for the `sync-upstream` script.

## File Status Legend

- **verbatim**: Copied as-is from upstream. Auto-updated by `sync-upstream`.
- **modified**: Forked with local changes. `sync-upstream` reports upstream
  diffs for manual review.
- **local**: No upstream equivalent. Ignored by `sync-upstream`.

## Files

```yaml
# Verbatim skills — auto-updated by sync
skills/test-driven-development/: verbatim
skills/systematic-debugging/: verbatim
skills/verification-before-completion/: verbatim
skills/receiving-code-review/: verbatim
skills/dispatching-parallel-agents/: verbatim
skills/using-superpowers/: verbatim
skills/writing-skills/: verbatim

# Verbatim supporting files in modified skills
skills/brainstorming/visual-companion.md: verbatim
skills/brainstorming/spec-document-reviewer-prompt.md: verbatim
skills/brainstorming/scripts/: verbatim
skills/writing-plans/plan-document-reviewer-prompt.md: verbatim
skills/subagent-driven-development/code-quality-reviewer-prompt.md: verbatim
skills/subagent-driven-development/implementer-prompt.md: verbatim
skills/subagent-driven-development/spec-reviewer-prompt.md: verbatim
skills/requesting-code-review/code-reviewer.md: verbatim

# Verbatim commands, agents, hooks
commands/brainstorm.md: verbatim
commands/execute-plan.md: verbatim
commands/write-plan.md: verbatim
agents/code-reviewer.md: verbatim
hooks/hooks.json: verbatim
hooks/run-hook.cmd: verbatim
hooks/session-start: verbatim
hooks/hooks-cursor.json: verbatim

# Modified skills — manual review on sync
skills/using-worktrees/SKILL.md:
  status: modified
  upstream_path: skills/using-git-worktrees/SKILL.md
skills/finishing-a-development-branch/SKILL.md:
  status: modified
skills/requesting-code-review/SKILL.md:
  status: modified
skills/brainstorming/SKILL.md:
  status: modified
skills/writing-plans/SKILL.md:
  status: modified
skills/executing-plans/SKILL.md:
  status: modified
skills/subagent-driven-development/SKILL.md:
  status: modified

# Local only — no upstream equivalent
skills/using-git-worktrees/SKILL.md: local
references/vcs-preamble.md: local
references/upstream-manifest.md: local
scripts/sync-upstream: local
```
