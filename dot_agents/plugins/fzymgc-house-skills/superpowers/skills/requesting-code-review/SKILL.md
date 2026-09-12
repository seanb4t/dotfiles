---
name: requesting-code-review
description: >-
  Use when completing tasks, implementing major features, or before merging
  to verify work meets requirements (supports git and jj)
metadata:
  author: fzymgc-house
  version: 0.1.0 # x-release-please-version
  upstream: obra/superpowers v5.0.7 (skills/requesting-code-review)
---

# Requesting Code Review

> **Before running any VCS commands, read `references/vcs-preamble.md` and use
> the appropriate commands for the detected VCS (git or jj).**

Dispatch superpowers:code-reviewer subagent to catch issues before they
cascade. The reviewer gets precisely crafted context for evaluation --
never your session's history. This keeps the reviewer focused on the work
product, not your thought process, and preserves your own context for
continued work.

**Core principle:** Review early, review often.

## VCS Detection

```bash
if jj root >/dev/null 2>&1; then
  VCS=jj
else
  VCS=git
fi
```

## When to Request Review

**Mandatory:**

- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**

- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get commit SHAs:**

**git:**

```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**jj:**

In jj, `@` is the empty working-copy commit. `@-` is the meaningful
commit (your latest change), and `@--` is its parent (the base for review).

```bash
BASE_SHA=$(jj log -r '@--' --no-graph -T 'commit_id.short(12)')
HEAD_SHA=$(jj log -r '@-' --no-graph -T 'commit_id.short(12)')
```

**2. Dispatch code-reviewer subagent:**

Use Task tool with superpowers:code-reviewer type, fill template at `code-reviewer.md`

**Placeholders:**

- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary

**3. Act on feedback:**

- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

**git:**

```text
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch superpowers:code-reviewer subagent]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
```

**jj:**

```text
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(jj log -r '@--' --no-graph -T 'commit_id.short(12)')
HEAD_SHA=$(jj log -r '@-' --no-graph -T 'commit_id.short(12)')

[Dispatch superpowers:code-reviewer subagent]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec3d2f1
  HEAD_SHA: 3df7661b8a04
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
```

## Integration with Workflows

**Subagent-Driven Development:**

- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**

- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**

- Review before merge
- Review when stuck

## Red Flags

**Never:**

- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**

- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: requesting-code-review/code-reviewer.md
