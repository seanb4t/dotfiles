---
name: finishing-a-development-branch
description: >-
  Use when implementation is complete, all tests pass, and you need to
  decide how to integrate the work (git or jj) - guides completion of
  development work by presenting structured options for merge, PR, or cleanup
metadata:
  author: fzymgc-house
  version: 0.1.0 # x-release-please-version
  upstream: obra/superpowers v5.0.7 (skills/finishing-a-development-branch)
---

# Finishing a Development Branch

> **Before running any VCS commands, read `references/vcs-preamble.md` and use
> the appropriate commands for the detected VCS (git or jj).**

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Verify tests → Present options → Execute choice → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## VCS Detection

```bash
if jj root >/dev/null 2>&1; then
  VCS=jj
else
  VCS=git
fi
```

## The Process

### Step 1: Verify Tests

**Before presenting options, verify tests pass:**

```bash
# Run project's test suite
npm test / cargo test / pytest / go test ./...
```

**If tests fail:**

```text
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 2.

**If tests pass:** Continue to Step 2.

### Step 2: Determine Base Branch

**git:**

```bash
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

**jj:**

```bash
# Find the trunk bookmark (main or master)
jj log -r 'trunk()' --no-graph -T 'bookmarks' --limit 1
```

Or ask: "This branch split from main - is that correct?"

### Step 3: Present Options

Present exactly these 4 options:

```text
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**Don't add explanation** - keep options concise.

### Step 4: Execute Choice

#### Option 1: Merge Locally

**git:**

```bash
# Switch to base branch
git checkout <base-branch>

# Pull latest
git pull

# Merge feature branch
git merge <feature-branch>

# Verify tests on merged result
<test command>

# If tests pass
git branch -d <feature-branch>
```

**jj:**

```bash
# Rebase feature onto base branch, skip commits that become empty
jj rebase -s <rev> -o main --skip-emptied

# Verify tests on merged result
<test command>

# If tests pass, delete the bookmark
jj bookmark delete <name>
```

Then: Cleanup workspace (Step 5)

#### Option 2: Push and Create PR

**git:**

```bash
# Push branch
git push -u origin <feature-branch>

# Create PR
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
```

**jj:**

```bash
# Set bookmark and push
jj bookmark set <name> -r @-
jj git push -b <name>

# Create PR
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
```

Then: Cleanup workspace (Step 5)

#### Option 3: Keep As-Is

Report: "Keeping branch <name>. Workspace preserved at <path>."

**Don't cleanup workspace.**

#### Option 4: Discard

**Confirm first:**

```text
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Workspace at <path>

Type 'discard' to confirm.
```

Wait for exact confirmation.

If confirmed:

**git:**

```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

**jj:**

```bash
jj abandon <rev>
jj bookmark delete <name>
```

Then: Cleanup workspace (Step 5)

### Step 5: Cleanup Workspace

**For Options 1, 2, 4:**

**git:**

Check if in worktree:

```bash
git worktree list | grep $(git branch --show-current)
```

If yes:

```bash
git worktree remove <worktree-path>
```

**jj:**

```bash
jj workspace forget <name>
rm -rf <path>
```

Note: `jj workspace forget` de-registers the workspace but does NOT
delete files -- you must `rm -rf` the directory after.

**For Option 3:** Keep workspace.

## Quick Reference

| Option | Merge | Push | Keep Workspace | Cleanup Branch |
|--------|-------|------|----------------|----------------|
| 1. Merge locally | yes | - | - | yes |
| 2. Create PR | - | yes | yes | - |
| 3. Keep as-is | - | - | yes | - |
| 4. Discard | - | - | - | yes (force) |

## Common Mistakes

**Skipping test verification**

- **Problem:** Merge broken code, create failing PR
- **Fix:** Always verify tests before offering options

**Open-ended questions**

- **Problem:** "What should I do next?" → ambiguous
- **Fix:** Present exactly 4 structured options

**Automatic workspace cleanup**

- **Problem:** Remove workspace when might need it (Option 2, 3)
- **Fix:** Only cleanup for Options 1 and 4

**No confirmation for discard**

- **Problem:** Accidentally delete work
- **Fix:** Require typed "discard" confirmation

**Using git commands in jj repos**

- **Problem:** `git checkout` / `git branch -D` corrupts jj state
- **Fix:** Always detect VCS first; use jj equivalents in jj repos

## Red Flags

**Never:**

- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push without explicit request
- Use git mutating commands in jj repos

**Always:**

- Detect VCS before running commands
- Verify tests before offering options
- Present exactly 4 options
- Get typed confirmation for Option 4
- Clean up workspace for Options 1 and 4 only

## Integration

**Called by:**

- **subagent-driven-development** (Step 7) - After all tasks complete
- **executing-plans** (Step 5) - After all batches complete

**Pairs with:**

- **using-worktrees** - Cleans up workspace created by that skill
