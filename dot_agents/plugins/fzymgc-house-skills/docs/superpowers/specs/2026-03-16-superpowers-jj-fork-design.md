# Superpowers Plugin Fork with jj (Jujutsu) VCS Support

## Overview

Fork the upstream `obra/superpowers` plugin (v5.0.2) into this repository as a
drop-in replacement that supports both git and jj (Jujutsu) VCS operations.
The forked plugin lives alongside `homelab`, `pr-review`, and `jj` as the
fourth plugin in this marketplace repo.

## Motivation

The upstream superpowers skills are 100% git-exclusive. Seven of the fourteen
skills contain hardcoded git commands for worktree management, branch
lifecycle, code review diffs, and commit workflows. In repositories that use
jj (including colocated git+jj repos), these skills produce incorrect commands,
create git worktrees instead of jj workspaces, and miss jj-specific
requirements like bookmarks, `--skip-emptied` rebases, and change IDs.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Deployment model | Fork into this repo as `superpowers/` plugin | Shares VCS infrastructure with existing `jj` and `pr-review` plugins; single repo to maintain |
| VCS abstraction | Shared preamble reference file | Each modified skill references `references/vcs-preamble.md`; skills use abstract operations mapped to concrete commands by the preamble |
| Fork scope | All 14 skills; modify 7, keep 7 verbatim | Clean break from upstream, no plugin name collisions, zero-touch for unmodified skills |
| Plugin name | `superpowers` | Drop-in replacement; existing CLAUDE.md references and skill triggers work unchanged |
| VCS reference | Self-contained within plugin | `references/vcs-preamble.md` tailored to worktree/workspace operations; no cross-plugin dependency |
| Worktree/workspace paths | Sibling directory pattern | `<repo>_worktrees/<name>` avoids nested repos that confuse LSP servers; matches existing pr-review convention |
| Upstream sync | Script with manifest-driven auto-update | Verbatim skills auto-updated; modified skills produce diff reports for Claude Code to review and apply |
| Upstream baseline | v5.0.2 (current as of 2026-03-16) | |
| jj rebase destination flag | `-o` / `--onto` (not `-d`) | `-d`/`--destination` deprecated per jj CHANGELOG; verified via DeepWiki against jj source |

## Plugin Configuration

### `plugin.json`

```json
{
  "name": "superpowers",
  "description": "Development workflow skills with git and jj VCS support (fork of obra/superpowers)",
  "version": "0.1.0"
}
```

No hooks needed in this plugin. VCS detection happens per-skill via the
preamble reference. The existing `jj` plugin's `guard-git-mutating` hook
coexists safely: it only activates in jj repos (`test -d .jj`), and in jj
repos the superpowers skills use jj commands (via the preamble), so the guard
never fires against superpowers-issued commands.

### Skill Registration and Backward Compatibility

Claude Code discovers skills by scanning `skills/*/SKILL.md` directories. The
renamed `using-worktrees` skill needs backward compatibility for existing
references to `using-git-worktrees`.

**Mechanism:** Create a second skill directory `skills/using-git-worktrees/`
containing a minimal `SKILL.md` that redirects:

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

This ensures `superpowers:using-git-worktrees` resolves and redirects to the
real skill. The redirect SKILL.md is marked `verbatim: false` (local) in the
upstream manifest since it has no upstream equivalent.

### External Reference Updates

On installation, the user should update:

- `~/.claude/CLAUDE.md`: update `using-git-worktrees` references to
  `using-worktrees` in the Full Skills Catalog
- `~/.claude/settings.json`: update any `Skill(superpowers:using-git-worktrees)`
  entries in allowed-tools to `Skill(superpowers:using-worktrees)`

The redirect skill provides backward compatibility during the transition, but
canonical references should use the new name.

## Plugin Structure

```text
superpowers/
  plugin.json                              # name: "superpowers"
  references/
    vcs-preamble.md                        # VCS detection + command mapping
    upstream-manifest.md                   # Tracks upstream version, per-file status
  scripts/
    sync-upstream                          # Upstream sync tool
  commands/                                # Slash commands (verbatim from upstream)
    brainstorm.md
    execute-plan.md
    write-plan.md
  agents/                                  # Agents (review for git-specific content)
    code-reviewer.md
  hooks/                                   # Hooks (review for git-specific content)
    hooks.json
    session-start
  skills/
    # Heavy modifications
    using-worktrees/SKILL.md               # Was using-git-worktrees; VCS-agnostic workspace creation
    finishing-a-development-branch/SKILL.md # Merge/PR/cleanup with VCS abstraction
    requesting-code-review/SKILL.md        # VCS-aware diff ranges
    requesting-code-review/code-reviewer.md

    # Light modifications
    brainstorming/SKILL.md                 # VCS-aware commit step
    brainstorming/visual-companion.md      # Verbatim
    brainstorming/spec-document-reviewer-prompt.md  # Verbatim
    brainstorming/scripts/                 # Verbatim (visual companion server)
    writing-plans/SKILL.md                 # VCS-aware task examples
    writing-plans/plan-document-reviewer-prompt.md  # Verbatim
    executing-plans/SKILL.md               # Updated skill references only
    subagent-driven-development/SKILL.md   # Updated skill references only
    subagent-driven-development/code-quality-reviewer-prompt.md  # Verbatim
    subagent-driven-development/implementer-prompt.md            # Verbatim
    subagent-driven-development/spec-reviewer-prompt.md          # Verbatim

    # Backward compatibility redirect
    using-git-worktrees/SKILL.md         # Redirect to using-worktrees

    # Verbatim copies (no modifications) — includes all supporting files
    test-driven-development/
    systematic-debugging/
    verification-before-completion/
    receiving-code-review/
    dispatching-parallel-agents/
    using-superpowers/
    writing-skills/
```

Note: Verbatim skill directories include ALL files from upstream (supporting
docs, scripts, examples), not just SKILL.md. The upstream manifest tracks
individual files for modified skills and directory-level status for verbatim
skills.

## VCS Preamble (`references/vcs-preamble.md`)

Each modified skill includes this instruction near the top of its SKILL.md
body (after frontmatter):

> **Before running any VCS commands, read `references/vcs-preamble.md` and use
> the appropriate commands for the detected VCS (git or jj).**

This is a plain-text instruction in the skill body, not a YAML frontmatter
field or markdown include directive. Claude Code reads it as part of the skill
content and follows it.

### Detection

```bash
if jj root >/dev/null 2>&1; then
  VCS=jj
else
  VCS=git
fi
```

### Command Mapping

| Operation | git | jj |
|-----------|-----|-----|
| Create workspace | `git worktree add ../<repo>_worktrees/<name> -b <branch>` | `jj workspace add ../<repo>_worktrees/<name> --name <name>` |
| List workspaces | `git worktree list` | `jj workspace list` |
| Remove workspace | `git worktree remove <path>` | `jj workspace forget <name>` + `rm -rf <path>` |
| Commit | `git add <files> && git commit -m "msg"` | `jj commit -m "msg"` |
| Describe/amend | `git commit --amend -m "msg"` | `jj describe -m "msg"` |
| New change | N/A (implicit) | `jj new` |
| Create branch/bookmark | `git checkout -b <name>` | `jj bookmark create <name> -r @` |
| Push | `git push -u origin <branch>` | `jj bookmark set <name> -r @ && jj git push -b <name>` |
| Fetch | `git fetch` / `git pull` | `jj git fetch` |
| Diff range (review) | `git diff <base_sha>..<head_sha>` | `jj diff --from <rev1> --to <rev2>` |
| Integrate fix | `git cherry-pick <sha>` | `jj rebase -r <change-id> -o <target>` |
| Merge to main | `git checkout main && git merge <branch>` | `jj rebase -s <rev> -o main --skip-emptied` |
| Delete branch/bookmark | `git branch -d <name>` | `jj bookmark delete <name>` |
| Force delete | `git branch -D <name>` | `jj abandon <rev>` + `jj bookmark delete <name>` |
| Current location | `git branch --show-current` | `jj log -r @ --no-graph -T 'change_id.short(8)'` |
| Status | `git status` | `jj st` |

### jj-Specific Rules

- Always `jj git fetch` at task start
- Always `jj commit -m "..."` before `jj new` (prevents lost-work footgun)
- Use change IDs, not commit hashes (stable across rewrites)
- Do not rewrite commits that have been pushed
- Use `--skip-emptied` for cleanup rebases
- Prefer `jj rebase --skip-emptied` over manual `jj abandon`

## Per-Skill Modification Details

### Heavy Modifications

#### `using-worktrees` (was `using-git-worktrees`)

Rename to drop "git-" prefix. Complete rewrite of workspace creation logic.

**Removed from upstream:**

- Nested `.worktrees/` / `worktrees/` directory selection
- `git check-ignore` verification
- `~/.config/superpowers/worktrees/` global fallback
- User prompt for directory choice

**Replaced with:**

- Sibling directory pattern: `<repo>_worktrees/<name>`
- VCS detection from preamble
- git: `git worktree add ../<repo>_worktrees/<name> -b <branch>`
- jj: `jj workspace add ../<repo>_worktrees/<name> --name <name>` + bookmark creation
- Cleanup: git = `git worktree remove`; jj = `jj workspace forget` + `rm -rf`

**Preserved from upstream:**

- Project setup auto-detection (package.json, Cargo.toml, etc.)
- Baseline test verification
- Integration section (called by brainstorming, executing-plans, subagent-driven-development)

**Registration:** Register as `using-worktrees` in plugin.json. Also register
`using-git-worktrees` as an alias so existing references (CLAUDE.md, other
skills) do not break.

#### `finishing-a-development-branch`

Add VCS preamble reference. Rewrite the four completion options:

| Option | git | jj |
|--------|-----|-----|
| Merge locally | `git checkout main && git pull && git merge <branch> && git branch -d <branch>` | `jj rebase -s <rev> -o main --skip-emptied && jj bookmark delete <name>` |
| Push + PR | `git push -u origin <branch>` + `gh pr create` | `jj bookmark set <name> -r @ && jj git push -b <name>` + `gh pr create` |
| Keep | No VCS commands | No VCS commands |
| Discard | `git branch -D <branch>` + `git worktree remove <path>` | `jj abandon <rev>` + `jj bookmark delete <name>` + `jj workspace forget <name>` + `rm -rf <path>` |

Worktree detection: git = `git worktree list`; jj = `jj workspace list`.

#### `requesting-code-review` (+ `code-reviewer.md`)

Add VCS preamble reference. Replace diff range commands:

- git: `git rev-parse HEAD~1` / `git rev-parse HEAD` for `{BASE_SHA}..{HEAD_SHA}`
- jj: `jj log -r @-- --no-graph -T 'commit_id.short(12)'` (base) / `jj log -r @- --no-graph -T 'commit_id.short(12)'` (head)
- Note: in jj, `@` is the empty working-copy commit; `@-` is the meaningful
  committed state; `@--` is its parent (the base for review)
- Diff command: git = `git diff`; jj = `jj diff --from @-- --to @-`

### Light Modifications

#### `brainstorming`

Add one line referencing VCS preamble for the commit step (step 7 in
checklist). Replace hardcoded `git commit` with "commit using VCS-appropriate
commands per `references/vcs-preamble.md`."

#### `writing-plans`

Task execution examples reference git commit commands. Add VCS note: "Use
VCS-appropriate commands per `references/vcs-preamble.md`."

#### `executing-plans`

Update reference from `using-git-worktrees` to `using-worktrees`. No other
changes.

#### `subagent-driven-development`

Update reference from `using-git-worktrees` to `using-worktrees`. No other
changes.

### No Modifications

Copied verbatim from upstream v5.0.2:

- `test-driven-development`
- `systematic-debugging`
- `verification-before-completion`
- `receiving-code-review`
- `dispatching-parallel-agents`
- `using-superpowers`
- `writing-skills`

## Upstream Sync Tool

### `scripts/sync-upstream`

Executable script that fetches the latest upstream release and reconciles
changes.

**Behavior:**

1. Fetch latest `obra/superpowers` release tag from GitHub via `gh api`
2. Download and extract to a temp directory
3. Read `references/upstream-manifest.md` for per-file modification status
4. For `verbatim` files: auto-copy new version in place
5. For `modified` files: generate a structured diff report to stdout
6. For new upstream files not in manifest: report for manual triage
7. Update `upstream-manifest.md` with new version and sync date

**Output format (for modified files):**

```text
=== MODIFIED SKILL: skills/using-worktrees/SKILL.md ===
Upstream source: skills/using-git-worktrees/SKILL.md
Local status: modified

--- Upstream changes since v5.0.2 ---
<unified diff of upstream changes>

--- Action required ---
Review upstream changes and apply relevant improvements while
preserving VCS preamble integration and sibling-dir workspace pattern.
```

**Claude Code operability:** A future Claude Code session can run the script,
read the structured output, and apply upstream improvements to modified skills
while preserving the VCS abstraction layer. The manifest provides the context
needed to make informed merge decisions.

### `references/upstream-manifest.md`

Tracks upstream version and per-file modification status. Format:

```yaml
upstream_repo: obra/superpowers
upstream_version: 5.0.2
synced_at: 2026-03-16

files:
  # Verbatim — auto-updated by sync
  skills/test-driven-development/SKILL.md: verbatim
  skills/systematic-debugging/SKILL.md: verbatim
  skills/verification-before-completion/SKILL.md: verbatim
  skills/receiving-code-review/SKILL.md: verbatim
  skills/dispatching-parallel-agents/SKILL.md: verbatim
  skills/using-superpowers/SKILL.md: verbatim
  skills/writing-skills/SKILL.md: verbatim
  skills/brainstorming/visual-companion.md: verbatim
  skills/brainstorming/spec-document-reviewer-prompt.md: verbatim

  # Modified — manual review on sync
  # Format: local_path: {status, upstream_path (if renamed)}
  skills/using-worktrees/SKILL.md:
    status: modified
    upstream_path: skills/using-git-worktrees/SKILL.md
  skills/finishing-a-development-branch/SKILL.md:
    status: modified
  skills/requesting-code-review/SKILL.md:
    status: modified
  skills/requesting-code-review/code-reviewer.md:
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
  skills/using-git-worktrees/SKILL.md: local  # backward compat redirect
  references/vcs-preamble.md: local
  references/upstream-manifest.md: local
  scripts/sync-upstream: local
```

## Release & Integration

### Release-please

Follow the `jj` plugin pattern: plugin root + per-skill entries for modified
skills only. Verbatim skills don't need individual version tracking (they
change via sync-upstream, which bumps the plugin root version).

**`release-please-config.json`:** Add these packages:

```json
"superpowers": {
  "release-type": "simple",
  "package-name": "superpowers",
  "extra-files": [
    { "type": "json", "path": "superpowers/plugin.json", "jsonpath": "$.version" }
  ]
},
"superpowers/skills/using-worktrees": {
  "release-type": "simple",
  "package-name": "using-worktrees",
  "extra-files": [
    { "type": "generic", "path": "superpowers/skills/using-worktrees/SKILL.md" }
  ]
},
"superpowers/skills/finishing-a-development-branch": { ... },
"superpowers/skills/requesting-code-review": { ... },
"superpowers/skills/brainstorming": { ... },
"superpowers/skills/writing-plans": { ... },
"superpowers/skills/executing-plans": { ... },
"superpowers/skills/subagent-driven-development": { ... }
```

**`.release-please-manifest.json`:** Add entries:

```json
"superpowers": "0.1.0",
"superpowers/skills/using-worktrees": "0.1.0",
"superpowers/skills/finishing-a-development-branch": "0.1.0",
"superpowers/skills/requesting-code-review": "0.1.0",
"superpowers/skills/brainstorming": "0.1.0",
"superpowers/skills/writing-plans": "0.1.0",
"superpowers/skills/executing-plans": "0.1.0",
"superpowers/skills/subagent-driven-development": "0.1.0"
```

CI validates that skill directories and release-please config stay in sync
(existing repo pattern).

### Marketplace Updates

Add the `superpowers` plugin to `.claude-plugin/marketplace.json` with
appropriate metadata (name, description, version, skill list).

### CLAUDE.md Updates

- Add `superpowers` to the Available Skills section with note that it replaces
  upstream `obra/superpowers`
- Update `using-git-worktrees` references to `using-worktrees` in the Full
  Skills Catalog table
- Document `scripts/sync-upstream` in the Development section

### Installation

```bash
claude plugin uninstall superpowers    # Remove upstream
claude plugin install .                # Install from this repo
```

### Testing

Each modified skill should be verified in both VCS modes:

- [ ] VCS detection correctly identifies git-only vs jj repos
- [ ] `using-worktrees`: creates sibling-dir workspace with correct VCS commands
- [ ] `finishing-a-development-branch`: all 4 options work in both VCS modes
- [ ] `requesting-code-review`: correct diff range commands for both VCS
- [ ] `brainstorming`: commits design docs with correct VCS commands
- [ ] `gh pr create` works in both modes (jj colocated repos have `.git/`)
- [ ] Verbatim skills work unchanged
- [ ] `sync-upstream` correctly fetches, compares, and reports
