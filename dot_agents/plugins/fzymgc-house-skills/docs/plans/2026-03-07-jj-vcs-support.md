# jj (Jujutsu) VCS Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task.

**Goal:** Add jj VCS support so skills detect `.jj/` and use jj
for all VCS operations, with a new jj plugin, adapted pr-review
skills/agents, and VCS-aware isolation hooks.

**Architecture:** New `jj/` plugin provides jujutsu workflow guidance
and `/jj-init` command. pr-review skills/agents get a VCS detection
preamble referencing a shared equivalence table. Worktree hooks become
VCS-aware, using `jj workspace` in jj repos.

**Tech Stack:** Markdown (SKILL.md, agent .md), JSON (plugin.json,
release configs), Bash (hooks)

**Design doc:** `docs/plans/2026-03-07-jj-vcs-support-design.md`

---

## Task 1: Create jj Plugin Scaffold

**Files:** Create `jj/plugin.json`

### Step 1: Create plugin.json

```json
{
  "name": "jj",
  "version": "0.1.0",
  "description": "Jujutsu (jj) VCS workflow guidance for colocated repos"
}
```

#### Step 2: Verify structure

Run: `ls jj/plugin.json` — file exists.

#### Step 3: Commit

```bash
git add jj/plugin.json
git commit -m "feat(jj): add plugin scaffold"
```

---

## Task 2: Create jj-git-interop Reference

**Files:** Create `jj/skills/jujutsu/references/jj-git-interop.md`

### Step 1: Write the interop reference

Consult jj docs at `https://jj-vcs.github.io/jj/latest/` via context7.
Cover these topics:

- Colocated repo behavior (`.jj/` + `.git/` coexist, auto-sync)
- Bookmark-to-branch sync (auto-imported/exported)
- Push/fetch (`jj git push --bookmark`, `jj git fetch`)
- Detached HEAD (normal/expected in jj)
- `gh` CLI compatibility (works because `.git/` exists)
- Workspace behavior (shared repo, changes visible across)
- What NOT to do (no mutating `git` commands in colocated repos)

Keep under 100 lines. Reference jj docs URLs where helpful.

#### Step 2: Verify

Run: `rumdl check jj/skills/jujutsu/references/jj-git-interop.md`
— no errors.

#### Step 3: Commit

```bash
git add jj/skills/jujutsu/references/jj-git-interop.md
git commit -m "docs(jj): add jj-git interop reference"
```

---

## Task 3: Create jujutsu SKILL.md

**Files:** Create `jj/skills/jujutsu/SKILL.md`

### Step 1: Write the skill

Base on danverbraganza/jujutsu-skill (MIT license). Fetch via
WebFetch for reference.

YAML frontmatter:

```yaml
---
name: jujutsu
description: >-
  Jujutsu (jj) VCS workflow guidance. MUST activate on ANY VCS
  operation when `.jj/` exists in the repo root. Use when the user
  mentions jj, jujutsu, or when a colocated jj repo is detected.
allowed-tools:
  - "Bash(jj *)"
metadata:
  author: fzymgc-house
  version: 0.1.0 # x-release-please-version
---
```

Body sections (keep under 500 lines total):

1. Detection — check `.jj/` in repo root
2. Agent Environment Rules — `-m` flags, no interactive commands
3. Core Concepts — working copy = commit, no staging, mutable history
4. Essential Workflow — `jj desc`, `jj new`, `jj commit`, `jj log`,
   `jj diff`, `jj show`
5. Refining Commits — `jj squash`, `jj absorb`, `jj abandon`,
   `jj undo`, `jj restore` (NOT `jj split` — interactive)
6. Bookmarks — create/move/list/delete, must update before pushing
7. Workspaces — add/forget/list, each has own `@`
8. Git Integration — reference `references/jj-git-interop.md`
9. Conflict Handling — can commit conflicts, resolve by editing
10. Quick Reference — command table
11. See Also — mention `jjagent` plugin for session-level mgmt

#### Step 2: Verify

Run: `rumdl check jj/skills/jujutsu/SKILL.md` — no errors.
Run: `wc -l jj/skills/jujutsu/SKILL.md` — under 500 lines.

#### Step 3: Commit

```bash
git add jj/skills/jujutsu/SKILL.md
git commit -m "feat(jj): add jujutsu skill"
```

---

## Task 4: Create /jj-init Command

**Files:** Create `jj/commands/jj-init.md`

### Step 1: Write the command

YAML frontmatter with `name: jj-init`, `user_invocable: true`,
allowed-tools for `Bash(jj *)`, `Bash(git *)`, Read, Edit, Write.

Body steps:

1. Check prerequisites — `git rev-parse --show-toplevel`
2. Check if already initialized — `test -d .jj`
3. Initialize — `jj git init --colocate` (`--colocate` required for colocation)
4. Add `.jj/` to `.gitignore` if not present
5. Verify — `jj st` and `jj log --no-graph -n 3`

#### Step 2: Verify

Run: `rumdl check jj/commands/jj-init.md` — no errors.

#### Step 3: Commit

```bash
git add jj/commands/jj-init.md
git commit -m "feat(jj): add /jj-init command"
```

---

## Task 5: Create VCS Equivalence Reference

**Files:** Create `pr-review/references/vcs-equivalence.md`

### Step 1: Write the equivalence table

Full git-to-jj command mapping. Include these operations:

| Operation | git | jj |
|-----------|-----|-----|
| Status | `git status --porcelain` | `jj st` |
| Diff (working copy) | `git diff` | `jj diff` |
| Diff (specific rev) | `git diff <ref>` | `jj diff -r <ref>` |
| Diff (range) | `git diff A..B` | `jj diff --from A --to B` |
| Log | `git log --oneline` | `jj log --no-graph` |
| Show commit | `git show <ref>` | `jj show <ref>` |
| Current location | `git branch --show-current` | `jj log -r @ --no-graph -n 1` |
| File list | `git ls-files` | `jj file list` |
| Stage + commit | `git add && git commit -m` | `jj commit -m "..."` |
| Push | `git push` | `jj git push -b <name>` |
| Fetch | `git fetch` | `jj git fetch` |
| Cherry-pick | `git cherry-pick <sha>` | `jj rebase -r <id> -d <target>` |
| Undo | `git reset`/`git revert` | `jj undo` |
| Create workspace | `git worktree add` | `jj workspace add` |
| Remove workspace | `git worktree remove` | `jj workspace forget` + rm |
| List workspaces | `git worktree list` | `jj workspace list` |

Also include: key differences section, agent output format
(CHANGE_ID vs WORKTREE_BRANCH), operations that stay git/gh,
and `jj git push --change <id>` shortcut (auto-generates bookmark).

#### Step 2: Verify

Run: `rumdl check pr-review/references/vcs-equivalence.md` — no errors.

#### Step 3: Commit

```bash
git add pr-review/references/vcs-equivalence.md
git commit -m "docs(pr-review): add VCS equivalence reference"
```

---

## Task 6: Add VCS Detection Preamble to pr-review Skills

**Files:**

- Modify: `pr-review/skills/address-findings/SKILL.md`
- Modify: `pr-review/skills/review-pr/SKILL.md`
- Modify: `pr-review/skills/respond-to-comments/SKILL.md`

### Step 1: Read each SKILL.md

Identify insertion point: after YAML frontmatter description, before
first `## Phase` or operational heading.

#### Step 2: Add VCS detection preamble

Insert a `## VCS Detection` section with:
`test -d .jj && echo "jj" || echo "git"` detection, instructions
to use `references/vcs-equivalence.md` for jj repos, and note
that `gh` CLI is VCS-independent.

#### Step 3: Add jj to allowed-tools

Add `"Bash(jj *)"` to each skill's `allowed-tools` list.

#### Step 4: Update address-findings Phase 4b

Rename to "Phase 4b: Integrate Fix Commits". Add git and jj
sub-sections. git: cherry-pick flow (unchanged). jj: rebase
flow using CHANGE_ID, `jj rebase`, `jj bookmark set`
(creates or moves), `jj workspace forget`.

#### Step 5: Update address-findings Phase 1

Add jj context to PR checkout: after `gh pr checkout`,
run `jj new <pr-bookmark>` in jj repos.

#### Step 6: Update address-findings Phase 6

Add jj push: `jj git push --bookmark <pr-bookmark>`.

#### Step 7: Verify

Run: `rumdl check pr-review/skills/*/SKILL.md` — no errors.

#### Step 8: Commit

```bash
git add pr-review/skills/*/SKILL.md
git commit -m "feat(pr-review): add VCS detection and jj support to skills"
```

---

## Task 7: Add VCS Detection to pr-review Agents

**Files:** All 12 agents in `pr-review/agents/`.

### Step 1: Update Environment block (11 worktree agents)

All except review-gate. Replace the git-specific Environment block
with a VCS-detecting version: `test -d .jj` detection, jj startup
commands (`jj workspace root`, `jj log -r @`), git startup commands
(`git branch --show-current`, worktree branch check).

#### Step 2: Update fix-worker commit step

Replace git-only commit with VCS-conditional:

- git: `git add <files> && git commit -m "fix(...)"`
- jj: `jj commit -m "fix(...)"`

#### Step 3: Update fix-worker output format

Add `CHANGE_ID` field for jj repos alongside `WORKTREE_BRANCH`
for git repos. Report whichever matches the VCS.

#### Step 4: Update verification-runner commit step

Add jj alternative for lint fix commits:

- git: `git add && git commit -m "fix(lint): ..."`
- jj: `jj commit -m "fix(lint): ..."`

#### Step 5: Update review-gate references

Change "git diff" to "VCS diff" in description and input sections.
The review-gate receives diffs from the orchestrator, so no VCS
detection needed — just terminology.

#### Step 6: Verify

Run: `rumdl check pr-review/agents/*.md` — no errors.

#### Step 7: Commit

```bash
git add pr-review/agents/*.md
git commit -m "feat(pr-review): add VCS detection to all agents"
```

---

## Task 8: Update Worktree Hooks for VCS-Aware Isolation

**Files:**

- Modify: `.claude/hooks/worktree-create.sh`
- Modify: `.claude/hooks/worktree-remove.sh`

### Step 1: Read current hooks

Verify structure before editing.

#### Step 2: Update worktree-create.sh

After `mkdir -p "$WORKTREE_PARENT"`, add VCS detection:

```bash
if [[ -d "${REPO_ROOT}/.jj" ]]; then
  (cd "$REPO_ROOT" && jj workspace add "$WORKTREE_PATH" \
    --name "worktree-${NAME}")
else
  git worktree add "$WORKTREE_PATH" -b "worktree/${NAME}" HEAD
  if [[ -f "${REPO_ROOT}/lefthook.yml" ]]; then
    (cd "$WORKTREE_PATH" && lefthook install 2>/dev/null) || true
  fi
fi
echo "$WORKTREE_PATH"
```

#### Step 3: Update worktree-remove.sh

Add VCS detection for cleanup:

```bash
WORKSPACE_NAME=$(basename "$WORKTREE_PATH")
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [[ -n "$REPO_ROOT" && -d "${REPO_ROOT}/.jj" ]]; then
  (cd "$REPO_ROOT" && jj workspace forget \
    "worktree-${WORKSPACE_NAME}") 2>/dev/null || true
  rm -rf "$WORKTREE_PATH"
else
  git worktree remove --force "$WORKTREE_PATH" 2>/dev/null || true
fi
```

#### Step 4: Test hooks

In a colocated test repo: create workspace, verify with
`jj workspace list`, remove, verify removed. In a pure git repo:
create worktree, verify with `git worktree list`, remove, verify.

#### Step 5: Commit

```bash
git add .claude/hooks/worktree-create.sh \
       .claude/hooks/worktree-remove.sh
git commit -m "feat: make worktree hooks VCS-aware for jj"
```

---

## Task 9: Update Release Config

**Files:**

- Modify: `release-please-config.json`
- Modify: `.release-please-manifest.json`
- Modify: `.claude-plugin/marketplace.json`

### Step 1: Add jj package to release-please-config.json

Add `"jj"` entry to packages with release-type simple, extra-files
for `jj/plugin.json` (jsonpath `$.version`) and
`jj/skills/jujutsu/SKILL.md` (generic).

#### Step 2: Add jj to manifest

Add `"jj": "0.1.0"` to `.release-please-manifest.json`.

#### Step 3: Add jj plugin to marketplace.json

Add entry to plugins array: name `jj`, description matching
plugin.json, source `./jj`.

#### Step 4: Commit

```bash
git add release-please-config.json \
       .release-please-manifest.json \
       .claude-plugin/marketplace.json
git commit -m "chore: add jj plugin to release config and marketplace"
```

---

## Task 10: Update CLAUDE.md

**Files:** Modify `CLAUDE.md` (root)

### Step 1: Update Available Skills section

Add jujutsu skill entry with description and activation trigger.

#### Step 2: Update Structure section

Add `jj/` directory tree to the structure diagram.

#### Step 3: Commit

```bash
git add CLAUDE.md
git commit -m "docs: add jj plugin to CLAUDE.md"
```

---

## Task 11: Manual Testing

No files to commit. Validates the full integration.

### Step 1: Test /jj-init

Create a temp git repo, invoke `/jj-init`, verify `.jj/` created,
`.gitignore` updated, `jj st` and `jj log` work.

#### Step 2: Test VCS detection

In a jj repo, trigger the jujutsu skill. Verify it uses `jj st`
instead of `git status`.

#### Step 3: Test workspace hooks

In a colocated repo: test create hook (verify `jj workspace list`
shows new workspace), test remove hook (verify workspace gone).

#### Step 4: Regression test

In a pure git repo: test create/remove hooks still use git
worktree commands correctly.

---

## Task 12: Update Memory

**Files:** Modify auto-memory `MEMORY.md`

### Step 1: Add jj plugin info

Update Plugin Architecture section with:

- Three-plugin marketplace (homelab + pr-review + jj)
- jj skills and commands
- VCS detection preamble pattern
- VCS-aware hook behavior
- Fix worker CHANGE_ID / WORKTREE_BRANCH output
- Cherry-pick to rebase transition in jj repos
- Complementary relationship with jjagent plugin
