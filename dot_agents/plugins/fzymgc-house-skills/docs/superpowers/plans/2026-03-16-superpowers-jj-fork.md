# Superpowers jj Fork Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development
> (if subagents available) or superpowers:executing-plans to implement this plan.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fork obra/superpowers v5.0.2 into this repo as a drop-in replacement
with jj (Jujutsu) VCS support.

**Architecture:** New `superpowers/` plugin directory alongside homelab,
pr-review, and jj. VCS abstraction via shared preamble reference file. Modified
skills detect git vs jj and use appropriate commands. Upstream sync tool for
future updates.

**Tech Stack:** Markdown skills, bash scripts, YAML/JSON config, gh CLI

**Spec:** `docs/superpowers/specs/2026-03-16-superpowers-jj-fork-design.md`

**Upstream source:** `/Users/sean/.claude/plugins/cache/superpowers-marketplace/superpowers/5.0.2/`

---

## Chunk 1: Plugin Scaffolding

### Task 1: Create plugin.json and directory structure

**Files:**

- Create: `superpowers/plugin.json`

- [ ] **Step 1: Create plugin.json**

```json
{
  "name": "superpowers",
  "description": "Development workflow skills with git and jj VCS support (fork of obra/superpowers v5.0.2)",
  "version": "0.1.0"
}
```

- [ ] **Step 2: Verify directory exists**

Run: `ls superpowers/plugin.json`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add superpowers/plugin.json
git commit -m "feat(superpowers): scaffold plugin with plugin.json"
```

### Task 2: Create VCS preamble reference

**Files:**

- Create: `superpowers/references/vcs-preamble.md`

- [ ] **Step 1: Write the VCS preamble**

Write the full content of `references/vcs-preamble.md` as specified in the
design spec §VCS Preamble. Include:

- Detection logic (`jj root` check)
- Full command mapping table (17 operations, git + jj columns)
- jj-specific rules (6 rules)
- Sibling directory pattern for workspaces: `<repo>_worktrees/<name>`

Use the design spec's command mapping table verbatim — it was verified against
jj source via DeepWiki.

- [ ] **Step 2: Commit**

```bash
git add superpowers/references/vcs-preamble.md
git commit -m "feat(superpowers): add VCS preamble reference for git/jj abstraction"
```

### Task 3: Create upstream manifest

**Files:**

- Create: `superpowers/references/upstream-manifest.md`

- [ ] **Step 1: Write the manifest**

Write the full manifest as specified in the design spec §upstream-manifest.md.
Include YAML frontmatter with `upstream_repo`, `upstream_version`, `synced_at`,
and the complete `files` map with status and `upstream_path` for renamed files.

- [ ] **Step 2: Commit**

```bash
git add superpowers/references/upstream-manifest.md
git commit -m "feat(superpowers): add upstream manifest tracking obra/superpowers v5.0.2"
```

---

## Chunk 2: Verbatim Skill Copies

Copy the 7 unmodified skills from upstream with ALL supporting files.

### Task 4: Copy verbatim skills

**Files:**

- Create: `superpowers/skills/test-driven-development/SKILL.md`
- Create: `superpowers/skills/test-driven-development/testing-anti-patterns.md`
- Create: `superpowers/skills/systematic-debugging/SKILL.md`
- Create: `superpowers/skills/systematic-debugging/CREATION-LOG.md`
- Create: `superpowers/skills/systematic-debugging/condition-based-waiting.md`
- Create: `superpowers/skills/systematic-debugging/condition-based-waiting-example.ts`
- Create: `superpowers/skills/systematic-debugging/defense-in-depth.md`
- Create: `superpowers/skills/systematic-debugging/find-polluter.sh`
- Create: `superpowers/skills/systematic-debugging/root-cause-tracing.md`
- Create: `superpowers/skills/systematic-debugging/test-academic.md`
- Create: `superpowers/skills/systematic-debugging/test-pressure-1.md`
- Create: `superpowers/skills/systematic-debugging/test-pressure-2.md`
- Create: `superpowers/skills/systematic-debugging/test-pressure-3.md`
- Create: `superpowers/skills/verification-before-completion/SKILL.md`
- Create: `superpowers/skills/receiving-code-review/SKILL.md`
- Create: `superpowers/skills/dispatching-parallel-agents/SKILL.md`
- Create: `superpowers/skills/using-superpowers/SKILL.md`
- Create: `superpowers/skills/using-superpowers/references/codex-tools.md`
- Create: `superpowers/skills/using-superpowers/references/gemini-tools.md`
- Create: `superpowers/skills/writing-skills/SKILL.md`
- Create: `superpowers/skills/writing-skills/anthropic-best-practices.md`
- Create: `superpowers/skills/writing-skills/persuasion-principles.md`
- Create: `superpowers/skills/writing-skills/testing-skills-with-subagents.md`
- Create: `superpowers/skills/writing-skills/graphviz-conventions.dot`
- Create: `superpowers/skills/writing-skills/render-graphs.js`
- Create: `superpowers/skills/writing-skills/examples/CLAUDE_MD_TESTING.md`

- [ ] **Step 1: Copy all verbatim skills from upstream**

```bash
UPSTREAM="/Users/sean/.claude/plugins/cache/superpowers-marketplace/superpowers/5.0.2"
DEST="superpowers/skills"

for skill in test-driven-development systematic-debugging verification-before-completion \
             receiving-code-review dispatching-parallel-agents using-superpowers writing-skills; do
  cp -r "$UPSTREAM/skills/$skill" "$DEST/"
done
```

- [ ] **Step 2: Verify file count**

Run: `find superpowers/skills -type f | wc -l`
Expected: 26 files (the list above)

- [ ] **Step 3: Commit**

```bash
git add superpowers/skills/test-driven-development/ \
        superpowers/skills/systematic-debugging/ \
        superpowers/skills/verification-before-completion/ \
        superpowers/skills/receiving-code-review/ \
        superpowers/skills/dispatching-parallel-agents/ \
        superpowers/skills/using-superpowers/ \
        superpowers/skills/writing-skills/
git commit -m "feat(superpowers): copy 7 verbatim skills from upstream v5.0.2"
```

---

## Chunk 3: Heavy Skill Modifications

### Task 5: Create `using-worktrees` skill

**Files:**

- Create: `superpowers/skills/using-worktrees/SKILL.md`

- [ ] **Step 1: Copy upstream using-git-worktrees as starting point**

```bash
mkdir -p superpowers/skills/using-worktrees
cp "$UPSTREAM/skills/using-git-worktrees/SKILL.md" superpowers/skills/using-worktrees/SKILL.md
```

- [ ] **Step 2: Rewrite the skill**

Modify the copied SKILL.md per the design spec §using-worktrees:

1. Update YAML frontmatter: rename to `using-worktrees`, update description to
   mention both git worktrees and jj workspaces
2. Add VCS preamble instruction after frontmatter:
   > **Before running any VCS commands, read `references/vcs-preamble.md` and
   > use the appropriate commands for the detected VCS (git or jj).**
3. Replace "Directory Selection Process" with sibling-dir pattern:
   - Path: `../<repo>_worktrees/<name>`
   - Drop `.worktrees/`, `worktrees/`, `~/.config/superpowers/worktrees/` logic
   - Drop `git check-ignore` verification (sibling dirs don't need it)
   - Drop "Ask User" section
4. Replace "Creation Steps" with VCS-branched logic:
   - git: `git worktree add ../<repo>_worktrees/<name> -b <branch>`
   - jj: `jj workspace add ../<repo>_worktrees/<name> --name <name>` then
     `jj bookmark create <name> -r @`
   - jj extra: run `jj git fetch` at start
5. Update cleanup/removal section for both VCS
6. Update Quick Reference table
7. Update Common Mistakes section
8. Update Example Workflow for both VCS
9. Keep: project setup auto-detection, baseline test verification, Integration
   section (update skill name references)

- [ ] **Step 3: Verify skill is under 500 lines**

Run: `wc -l superpowers/skills/using-worktrees/SKILL.md`
Expected: < 500

- [ ] **Step 4: Commit**

```bash
git add superpowers/skills/using-worktrees/SKILL.md
git commit -m "feat(superpowers): add using-worktrees skill with git/jj VCS support"
```

### Task 6: Create backward-compat redirect for `using-git-worktrees`

**Files:**

- Create: `superpowers/skills/using-git-worktrees/SKILL.md`

- [ ] **Step 1: Write redirect skill**

```yaml
---
name: using-git-worktrees
description: >-
  Alias for using-worktrees. Use when starting feature work that needs
  isolation from current workspace.
---
This skill has been renamed to `using-worktrees`. Read and follow
`../using-worktrees/SKILL.md` instead.
```

- [ ] **Step 2: Commit**

```bash
git add superpowers/skills/using-git-worktrees/SKILL.md
git commit -m "feat(superpowers): add using-git-worktrees redirect for backward compat"
```

### Task 7: Modify `finishing-a-development-branch`

**Files:**

- Create: `superpowers/skills/finishing-a-development-branch/SKILL.md`

- [ ] **Step 1: Copy from upstream**

```bash
mkdir -p superpowers/skills/finishing-a-development-branch
cp "$UPSTREAM/skills/finishing-a-development-branch/SKILL.md" \
   superpowers/skills/finishing-a-development-branch/SKILL.md
```

- [ ] **Step 2: Modify the skill**

1. Add VCS preamble instruction after frontmatter
2. Add VCS detection at the start of the workflow
3. For each of the 4 options (Merge, Push+PR, Keep, Discard), add jj
   equivalents per the design spec §finishing-a-development-branch table
4. Replace `git worktree list` with VCS-branched worktree detection
5. Replace `git merge-base` with jj-equivalent for base branch detection
6. Update all branch/bookmark operations
7. Update worktree cleanup for jj (workspace forget + rm -rf)
8. Update references from `using-git-worktrees` to `using-worktrees`

- [ ] **Step 3: Commit**

```bash
git add superpowers/skills/finishing-a-development-branch/SKILL.md
git commit -m "feat(superpowers): add jj VCS support to finishing-a-development-branch"
```

### Task 8: Modify `requesting-code-review`

**Files:**

- Create: `superpowers/skills/requesting-code-review/SKILL.md`
- Create: `superpowers/skills/requesting-code-review/code-reviewer.md`

- [ ] **Step 1: Copy from upstream**

```bash
mkdir -p superpowers/skills/requesting-code-review
cp "$UPSTREAM/skills/requesting-code-review/SKILL.md" \
   superpowers/skills/requesting-code-review/SKILL.md
cp "$UPSTREAM/skills/requesting-code-review/code-reviewer.md" \
   superpowers/skills/requesting-code-review/code-reviewer.md
```

- [ ] **Step 2: Modify SKILL.md**

1. Add VCS preamble instruction after frontmatter
2. Replace SHA discovery:
   - git: `git rev-parse HEAD~1` / `git rev-parse HEAD`
   - jj: `jj log -r @-- --no-graph -T 'commit_id.short(12)'` (base) /
     `jj log -r @- --no-graph -T 'commit_id.short(12)'` (head)
   - Note: `@` is empty working copy; `@-` is meaningful committed state
3. Replace diff commands: git = `git diff`; jj = `jj diff --from @-- --to @-`

- [ ] **Step 3: Modify code-reviewer.md**

Update the subagent template to use VCS-appropriate diff commands. The template
receives `{BASE_SHA}` and `{HEAD_SHA}` — the parent skill fills these using
VCS-appropriate commands, so the template itself may need minimal changes.
Review and update any hardcoded `git diff` references.

- [ ] **Step 4: Commit**

```bash
git add superpowers/skills/requesting-code-review/
git commit -m "feat(superpowers): add jj VCS support to requesting-code-review"
```

---

## Chunk 4: Light Skill Modifications

### Task 9: Modify `brainstorming`

**Files:**

- Create: `superpowers/skills/brainstorming/SKILL.md`
- Create: `superpowers/skills/brainstorming/visual-companion.md` (verbatim)
- Create: `superpowers/skills/brainstorming/spec-document-reviewer-prompt.md` (verbatim)
- Create: `superpowers/skills/brainstorming/scripts/` (all verbatim)

- [ ] **Step 1: Copy entire brainstorming directory from upstream**

```bash
cp -r "$UPSTREAM/skills/brainstorming" superpowers/skills/
```

- [ ] **Step 2: Modify SKILL.md only**

1. Add VCS preamble instruction after frontmatter
2. In the "Write design doc" step (step 6), replace hardcoded `git commit`
   with: "Commit using VCS-appropriate commands per `references/vcs-preamble.md`"
3. Update reference from `using-git-worktrees` to `using-worktrees` in any
   Integration or cross-skill references

- [ ] **Step 3: Commit**

```bash
git add superpowers/skills/brainstorming/
git commit -m "feat(superpowers): add jj VCS support to brainstorming skill"
```

### Task 10: Modify `writing-plans`

**Files:**

- Create: `superpowers/skills/writing-plans/SKILL.md`
- Create: `superpowers/skills/writing-plans/plan-document-reviewer-prompt.md` (verbatim)

- [ ] **Step 1: Copy from upstream**

```bash
cp -r "$UPSTREAM/skills/writing-plans" superpowers/skills/
```

- [ ] **Step 2: Modify SKILL.md only**

1. Add VCS preamble instruction after frontmatter
2. In the Task Structure template, replace hardcoded `git add` / `git commit`
   example with VCS-aware note: "Commit using VCS-appropriate commands per
   `references/vcs-preamble.md`"
3. Update any cross-skill references from `using-git-worktrees` to
   `using-worktrees`

- [ ] **Step 3: Commit**

```bash
git add superpowers/skills/writing-plans/
git commit -m "feat(superpowers): add jj VCS support to writing-plans skill"
```

### Task 11: Modify `executing-plans`

**Files:**

- Create: `superpowers/skills/executing-plans/SKILL.md`

- [ ] **Step 1: Copy from upstream**

```bash
mkdir -p superpowers/skills/executing-plans
cp "$UPSTREAM/skills/executing-plans/SKILL.md" superpowers/skills/executing-plans/
```

- [ ] **Step 2: Modify SKILL.md**

Replace all references to `using-git-worktrees` with `using-worktrees`. No
other changes — this skill delegates VCS operations to the worktree and
finishing skills which have their own VCS support.

- [ ] **Step 3: Commit**

```bash
git add superpowers/skills/executing-plans/
git commit -m "feat(superpowers): update executing-plans skill references for VCS support"
```

### Task 12: Modify `subagent-driven-development`

**Files:**

- Create: `superpowers/skills/subagent-driven-development/SKILL.md`
- Create: `superpowers/skills/subagent-driven-development/code-quality-reviewer-prompt.md` (verbatim)
- Create: `superpowers/skills/subagent-driven-development/implementer-prompt.md` (verbatim)
- Create: `superpowers/skills/subagent-driven-development/spec-reviewer-prompt.md` (verbatim)

- [ ] **Step 1: Copy entire directory from upstream**

```bash
cp -r "$UPSTREAM/skills/subagent-driven-development" superpowers/skills/
```

- [ ] **Step 2: Modify SKILL.md only**

Replace all references to `using-git-worktrees` with `using-worktrees`. No
other changes — this skill delegates VCS operations to the worktree and
finishing skills which have their own VCS support.

- [ ] **Step 3: Commit**

```bash
git add superpowers/skills/subagent-driven-development/
git commit -m "feat(superpowers): update subagent-driven-development for VCS support"
```

---

## Chunk 5: Commands, Agents, and Hooks

### Task 13: Copy commands

**Files:**

- Create: `superpowers/commands/brainstorm.md`
- Create: `superpowers/commands/execute-plan.md`
- Create: `superpowers/commands/write-plan.md`

- [ ] **Step 1: Copy commands from upstream**

```bash
cp -r "$UPSTREAM/commands" superpowers/
```

- [ ] **Step 2: Review for git-specific content**

Read each command file. Commands are typically thin wrappers that invoke skills.
If any contain hardcoded git commands, add VCS preamble reference. Most likely
no changes needed.

- [ ] **Step 3: Commit**

```bash
git add superpowers/commands/
git commit -m "feat(superpowers): copy slash commands from upstream v5.0.2"
```

### Task 14: Copy agent

**Files:**

- Create: `superpowers/agents/code-reviewer.md`

- [ ] **Step 1: Copy agent from upstream**

```bash
cp -r "$UPSTREAM/agents" superpowers/
```

- [ ] **Step 2: Review for git-specific content**

Read the agent file. If it contains hardcoded git commands (likely for diff
operations), add VCS preamble reference and update commands.

- [ ] **Step 3: Commit**

```bash
git add superpowers/agents/
git commit -m "feat(superpowers): copy code-reviewer agent from upstream v5.0.2"
```

### Task 15: Copy and adapt hooks

**Files:**

- Create: `superpowers/hooks/hooks.json`
- Create: `superpowers/hooks/session-start`

- [ ] **Step 1: Read upstream hooks**

```bash
cat "$UPSTREAM/hooks/hooks.json"
cat "$UPSTREAM/hooks/session-start"
```

Understand what the hooks do before copying. The session-start hook likely
sets up environment or checks plugin state.

- [ ] **Step 2: Copy hooks (skip run-hook.cmd — Windows only)**

```bash
mkdir -p superpowers/hooks
cp "$UPSTREAM/hooks/hooks.json" superpowers/hooks/
cp "$UPSTREAM/hooks/session-start" superpowers/hooks/
```

- [ ] **Step 3: Review for git-specific content and adapt**

If session-start contains git commands, add VCS detection. Ensure the hook
doesn't conflict with the `jj` plugin's hooks (the `jj` plugin has its own
SessionStart hook that runs VCS detection).

- [ ] **Step 4: Commit**

```bash
git add superpowers/hooks/
git commit -m "feat(superpowers): copy and adapt hooks from upstream v5.0.2"
```

---

## Chunk 6: Upstream Sync Tool

### Task 16: Write sync-upstream script

**Files:**

- Create: `superpowers/scripts/sync-upstream`

- [ ] **Step 1: Write the script**

Write `superpowers/scripts/sync-upstream` as a bash script that:

1. Reads `upstream-manifest.md` to get current upstream version and file map
2. Fetches latest upstream tag via `gh api repos/obra/superpowers/tags --jq '.[0].name'`
3. If same version, report "Already up to date" and exit
4. Downloads upstream tarball to temp dir via
   `gh api repos/obra/superpowers/tarball/<tag>` and extracts
5. For each `verbatim` file in manifest: copies upstream file to local path
6. For each `modified` file: generates unified diff between upstream versions
   (old baseline vs new) and outputs structured report
7. For files in upstream not in manifest: reports as "NEW — needs triage"
8. Updates `upstream-manifest.md` with new version and date
9. Outputs summary: N files auto-updated, M files need review, K new files

The script should handle the `using-git-worktrees` → `using-worktrees` rename
using the `upstream_path` field in the manifest.

- [ ] **Step 2: Make executable**

```bash
chmod +x superpowers/scripts/sync-upstream
```

- [ ] **Step 3: Test with current version (should report "up to date")**

Run: `superpowers/scripts/sync-upstream`
Expected: "Already up to date at v5.0.2"

- [ ] **Step 4: Commit**

```bash
git add superpowers/scripts/sync-upstream
git commit -m "feat(superpowers): add upstream sync tool for tracking obra/superpowers"
```

---

## Chunk 7: Release Integration

### Task 17: Update release-please config

**Files:**

- Modify: `release-please-config.json`
- Modify: `.release-please-manifest.json`

- [ ] **Step 1: Add superpowers packages to release-please-config.json**

Add these entries to the `packages` object (see design spec §Release-please
for full JSON):

- `superpowers` (plugin root) — extra-files: `superpowers/plugin.json`
- `superpowers/skills/using-worktrees`
- `superpowers/skills/finishing-a-development-branch`
- `superpowers/skills/requesting-code-review`
- `superpowers/skills/brainstorming`
- `superpowers/skills/writing-plans`
- `superpowers/skills/executing-plans`
- `superpowers/skills/subagent-driven-development`

Each skill entry follows the pattern:

```json
"superpowers/skills/<name>": {
  "release-type": "simple",
  "package-name": "<name>",
  "extra-files": [
    { "type": "generic", "path": "superpowers/skills/<name>/SKILL.md" }
  ]
}
```

- [ ] **Step 2: Add versions to .release-please-manifest.json**

Add `"superpowers": "0.1.0"` and `"superpowers/skills/<name>": "0.1.0"` for
each of the 7 modified skills.

- [ ] **Step 3: Commit**

```bash
git add release-please-config.json .release-please-manifest.json
git commit -m "chore(superpowers): add release-please config for superpowers plugin"
```

### Task 18: Update CLAUDE.md

**Files:**

- Modify: `CLAUDE.md`

- [ ] **Step 1: Add superpowers to Available Skills**

In the "Available Skills" section, add an entry for the superpowers plugin
skills (using-worktrees, finishing-a-development-branch, etc.) with a note
that it replaces upstream `obra/superpowers`.

- [ ] **Step 2: Add to Structure section**

Add `superpowers/` to the directory structure diagram showing plugin.json,
skills/, references/, scripts/.

- [ ] **Step 3: Document sync-upstream**

In the Development section, add a note about `scripts/sync-upstream` for
keeping the fork current with upstream.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add superpowers fork to CLAUDE.md"
```

### Task 19: Update marketplace.json

**Files:**

- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read current marketplace.json**

Understand the existing structure and add a superpowers plugin entry.

- [ ] **Step 2: Add superpowers plugin entry**

Add the plugin with name, description, version, and skill listing.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore: add superpowers plugin to marketplace.json"
```

### Task 20: Document external reference updates

**Files:** (user's personal config — not committed to this repo)

- [ ] **Step 1: Note required user config updates**

After installation, the user should update their personal config:

- `~/.claude/CLAUDE.md`: update `using-git-worktrees` to `using-worktrees` in
  the Full Skills Catalog table
- `~/.claude/settings.json`: update any `Skill(superpowers:using-git-worktrees)`
  entries in allowed-tools to `Skill(superpowers:using-worktrees)`

Add a note about this to the plugin's README or CLAUDE.md entry so future
sessions know about the transition.

The backward-compat redirect skill (Task 6) ensures things work during the
transition, but canonical references should use the new name.

### Task 21: Final verification

- [ ] **Step 1: Verify all skill directories exist**

```bash
ls -d superpowers/skills/*/
```

Expected: 15 directories (14 skills + using-git-worktrees redirect)

- [ ] **Step 2: Verify plugin structure**

```bash
find superpowers -type f | sort
```

Review output matches expected structure from design spec.

- [ ] **Step 3: Run rumdl on all markdown files**

```bash
rumdl check superpowers/**/*.md
```

Fix any formatting issues.

- [ ] **Step 4: Run lefthook pre-commit**

```bash
lefthook run pre-commit
```

Expected: all checks pass

- [ ] **Step 5: Verify release-please config sync**

Confirm all skill directories have corresponding release-please entries (CI
validates this).

- [ ] **Step 6: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix(superpowers): address lint and formatting issues"
```
