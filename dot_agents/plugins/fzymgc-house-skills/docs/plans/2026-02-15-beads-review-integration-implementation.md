# Beads Review Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace JSONL temp-dir workflow with beads-backed persistence in review-pr and respond-to-pr-comments skills.

**Architecture:** Subagents create finding beads directly via `bd` CLI.
PR review parent bead links to epic (if exists). Both skills share state
through beads queries. Labels (`pr-review`, `pr-review-finding`,
`aspect:*`, `severity:*`, `turn:*`) distinguish review beads from
project issues.

**Tech Stack:** beads CLI (`bd`), GitHub CLI (`gh`), Markdown skill files, no new scripts.

**Design doc:** `docs/plans/2026-02-15-beads-review-integration-design.md`

---

## Task 1: Update review-pr allowed-tools

Add `bd` CLI patterns to the skill's allowed-tools so both the orchestrator
and subagents can create/query beads.

**Files:**

- Modify: `fzymgc-house/skills/review-pr/SKILL.md` (lines 10-33, allowed-tools block)

### Step 1: Add bd tool patterns**

Add after the existing `Bash(gh api *)` line in the allowed-tools block:

```yaml
  - "Bash(bd create *)"
  - "Bash(bd list *)"
  - "Bash(bd update *)"
  - "Bash(bd show *)"
  - "Bash(bd dep *)"
  - "Bash(bd query *)"
  - "Bash(bd config *)"
```

#### Step 2: Verify YAML validity

Run: `python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]).read().split('---')[1])" fzymgc-house/skills/review-pr/SKILL.md`
Expected: No error (exits 0)

#### Step 3: Commit

```text
git add fzymgc-house/skills/review-pr/SKILL.md
git commit -m "feat(review-pr): add bd CLI to allowed-tools"
```

---

### Task 2: Update respond-to-pr-comments allowed-tools

Same as Task 1 but for the respond skill.

**Files:**

- Modify: `fzymgc-house/skills/respond-to-pr-comments/SKILL.md` (lines 9-19, allowed-tools block)

#### Step 1: Add bd tool patterns

Add after the existing `Bash(gh *)` line:

```yaml
  - "Bash(bd create *)"
  - "Bash(bd list *)"
  - "Bash(bd update *)"
  - "Bash(bd show *)"
  - "Bash(bd dep *)"
  - "Bash(bd query *)"
  - "Bash(bd comments *)"
```

Note: `bd comments` instead of `bd config` — this skill needs to add comments
to beads but doesn't need to configure beads.

#### Step 2: Verify YAML validity

Run: `python3 -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]).read().split('---')[1])" fzymgc-house/skills/respond-to-pr-comments/SKILL.md`
Expected: No error (exits 0)

#### Step 3: Commit

```text
git add fzymgc-house/skills/respond-to-pr-comments/SKILL.md
git commit -m "feat(respond-to-pr-comments): add bd CLI to allowed-tools"
```

---

### Task 3: Replace JSONL output in all 9 agent reference files

Every agent reference file has two sections to replace:

- `## Output Format — JSONL` (starts with JSONL schema, severity mapping, examples)
- `## Output Convention` (write to `$REVIEW_DIR`, return terse summary)

Replace both with a single `## Bead Output` section. The replacement content
is the same for all 9 agents except for the aspect name and example values.

**Files:**

- Modify: `fzymgc-house/skills/review-pr/references/agent-code-reviewer.md`
- Modify: `fzymgc-house/skills/review-pr/references/agent-silent-failure-hunter.md`
- Modify: `fzymgc-house/skills/review-pr/references/agent-pr-test-analyzer.md`
- Modify: `fzymgc-house/skills/review-pr/references/agent-type-design-analyzer.md`
- Modify: `fzymgc-house/skills/review-pr/references/agent-comment-analyzer.md`
- Modify: `fzymgc-house/skills/review-pr/references/agent-security-auditor.md`
- Modify: `fzymgc-house/skills/review-pr/references/agent-api-contract-checker.md`
- Modify: `fzymgc-house/skills/review-pr/references/agent-spec-compliance.md`
- Modify: `fzymgc-house/skills/review-pr/references/agent-code-simplifier.md`

#### Step 1: Replace output sections in each file

For each agent file, delete everything from `## Output Format — JSONL` through
the end of `## Output Convention` (including the convention body), and replace
with:

````markdown
## Bead Output

Create a bead for each finding via `bd create`. The orchestrator provides
these variables in the task prompt: `PARENT_BEAD_ID`, `ASPECT`, `TURN`,
`PR_URL`.

### Creating Findings

```bash
bd create "<title — first sentence of finding>" \
  --parent $PARENT_BEAD_ID \
  --type <bug|task|feature> \
  --priority <0-3> \
  --labels "pr-review-finding,aspect:$ASPECT,severity:<critical|important|suggestion|praise>,turn:$TURN" \
  --external-ref "$PR_URL" \
  --description "<full details: what's wrong, file:line location, suggested fix>" \
  --silent
```

**Severity → priority mapping:**

| Severity | Priority | Default type |
|----------|----------|-------------|
| critical | 0 | bug |
| important | 1 | bug or task |
| suggestion | 2 | task |
| praise | 3 | task (label with `praise`) |

### Re-reviews (turn > 1)

Query prior findings for your aspect:

```bash
bd list --parent $PARENT_BEAD_ID --labels "aspect:$ASPECT" --status open --json
```

For each prior finding:

- **Resolved** (no longer applies): `bd update <id> --status closed`
- **Still present**: Leave open, do not create a duplicate
- **New issue**: Create a new bead with the current turn number

### Return to Orchestrator

Return only a terse summary (2-3 lines): finding counts by severity and the
single most critical item. Do NOT return JSONL or full finding details.
````

The `$ASPECT` value differs per file:

| File | ASPECT value |
|------|-------------|
| agent-code-reviewer.md | `code` |
| agent-silent-failure-hunter.md | `errors` |
| agent-pr-test-analyzer.md | `tests` |
| agent-type-design-analyzer.md | `types` |
| agent-comment-analyzer.md | `comments` |
| agent-security-auditor.md | `security` |
| agent-api-contract-checker.md | `api` |
| agent-spec-compliance.md | `spec` |
| agent-code-simplifier.md | `simplify` |

Each file's `## Bead Output` intro line should say the aspect name explicitly:
"The orchestrator provides these variables... Your aspect is `<ASPECT>`."

#### Step 2: Verify no JSONL references remain

Run: `grep -r "JSONL\|jsonl\|REVIEW_DIR" fzymgc-house/skills/review-pr/references/`
Expected: No matches

#### Step 3: Verify markdown lint passes

Run: `rumdl check fzymgc-house/skills/review-pr/references/agent-*.md`
Expected: No issues

#### Step 4: Commit

```text
git add fzymgc-house/skills/review-pr/references/
git commit -m "feat(review-pr): replace JSONL output with bead creation in all agent prompts"
```

---

### Task 4: Rewrite review-pr SKILL.md workflow

Replace the JSONL/temp-dir workflow with the beads workflow from the design doc.

**Files:**

- Modify: `fzymgc-house/skills/review-pr/SKILL.md`

#### Step 1: Rewrite Step 1 (Determine Scope)

Replace the current Step 1 content (lines ~77-113). Remove `mktemp` and
`$REVIEW_DIR`. Add:

- Check for existing PR review bead: `bd list --labels "pr-review,pr:<number>" --json`
- If found: re-review (turn N+1), read bead ID and current turn
- If not found: create PR review parent bead via `bd create`
- Include `--parent <epic-id>` only if an epic is found
- Gather PR context with `gh` (same as before)
- Prior review history from GitHub API (same as before) — but note this is
  supplementary; beads are the primary source for prior findings

#### Step 2: Rewrite Step 5 (Launch Subagents)

Replace the current Step 5 content. Remove JSONL file references. Each Task call:

1. Sets the `model` parameter per step 3
2. Includes the git diff or changed file contents as context
3. Includes the full system prompt from the reference file
4. Passes `PARENT_BEAD_ID`, `ASPECT`, `TURN`, `PR_URL` variables
5. Instructs the agent to create beads directly and return a 2-3 line summary

Keep the batched parallel execution (max 3 concurrent).

#### Step 3: Rewrite Step 6 (Aggregate Results)

Replace JSONL file reading with bead query:

```bash
bd list --parent <parent-bead-id> --status open --json
```

Group by priority/severity label, compile the same Markdown summary format.

#### Step 4: Rewrite Step 7 (Post Findings)

Replace with the new PR comment template from the design doc:

```markdown
<!-- pr-review:<bead-id> -->
## [bead-id] — PR Review

`bd list --parent <bead-id> --status open`

N critical · N important · N suggestions

---

### Critical

**Finding title** `<finding-bead-id>`
Up to two lines of summary.

### Important

...

### Suggestions

...
```

Remove the `rm -rf $REVIEW_DIR` cleanup step. Remove the `summary.md` temp
file approach (no longer needed).

#### Step 5: Remove JSONL schema documentation

Delete the JSONL schema section from the SKILL.md body (the `**JSONL schema**`
block and `**Output convention**` block). Replace with a reference to the
bead data model:

```markdown
**Bead schema**: Each subagent creates finding beads with type, priority,
labels (`aspect:*`, `severity:*`, `turn:*`), external-ref (PR URL), and
description (full details + location + suggested fix).
```

#### Step 6: Update Quick Checklist

Update the checklist items to reflect beads:

```text
- [ ] Determine scope (parse PR number + aspects, check for existing review bead)
- [ ] Select applicable agents based on changes and requested aspects
- [ ] Choose model per agent (sonnet default, opus for complex/security)
- [ ] Read agent prompts from `references/`
- [ ] Create PR review parent bead (or find existing for re-review)
- [ ] Launch subagents via Task tool (batched, max 3 concurrent)
- [ ] Aggregate results from beads into unified summary
- [ ] Offer to post findings as PR comment (confirm with user first)
```

#### Step 7: Verify no JSONL/REVIEW_DIR references remain

Run: `grep -n "JSONL\|jsonl\|REVIEW_DIR\|mktemp\|rm -rf" fzymgc-house/skills/review-pr/SKILL.md`
Expected: No matches

#### Step 8: Verify markdown lint passes

Run: `rumdl check fzymgc-house/skills/review-pr/SKILL.md`
Expected: No issues

#### Step 9: Verify skill is under 500 lines

Run: `wc -l fzymgc-house/skills/review-pr/SKILL.md`
Expected: Under 500 lines

#### Step 10: Commit

```text
git add fzymgc-house/skills/review-pr/SKILL.md
git commit -m "feat(review-pr): rewrite workflow to use beads instead of JSONL temp dirs"
```

---

### Task 5: Rewrite respond-to-pr-comments SKILL.md workflow

Add beads integration to the respond skill's workflow phases.

**Files:**

- Modify: `fzymgc-house/skills/respond-to-pr-comments/SKILL.md`

#### Step 1: Update Phase 1 (Setup)

After step 2 (read unacked comments), add steps 3-4:

3. Query beads for the PR review bead:

   ```bash
   bd list --labels "pr-review,pr:<number>" --json
   ```

   If found, load all child findings:

   ```bash
   bd list --parent <review-bead-id> --json
   ```

4. Cross-reference GitHub PR comments against existing finding beads via
   external-ref URLs. Identify: aligned comments, new comments, bot-only findings.

Keep existing steps (locate worktree, etc.) but renumber.

#### Step 2: Update Phase 2 (Categorize)

In Step 2a, add: if a PR comment matches an existing finding bead, note the
finding bead ID for linking in Phase 3.

#### Step 3: Update Phase 3 (Implement)

After sub-agent completes a fix:

1. If non-trivial, create a work bead:

   ```bash
   bd create "Fix: <description>" --type task --deps "discovered-from:<finding-bead-id>" --silent
   ```

2. Close the related finding bead: `bd update <finding-bead-id> --status closed`
3. Acknowledge the PR comment (same as before)

#### Step 4: Update Phase 4.5 (Independent Review)

The opus review sub-agent queries beads instead of just git diff:

```bash
bd list --parent <review-bead-id> --json
```

Validates closed findings are actually addressed.

#### Step 5: Update Phase 5 (Ship)

Replace the summary comment format with the new template:

```markdown
<!-- pr-review:<bead-id>:response -->
## [bead-id] — Review Response

`bd list --parent <bead-id>`

Addressed N/M · N deferred

| Finding | Status |
|---------|--------|
| <bead-id> | Fixed |
| <bead-id> | Deferred — reason |
```

#### Step 6: Verify no stale references

Run: `grep -n "JSONL\|jsonl\|REVIEW_DIR" fzymgc-house/skills/respond-to-pr-comments/SKILL.md`
Expected: No matches (there shouldn't have been any, but verify)

#### Step 7: Verify markdown lint passes

Run: `rumdl check fzymgc-house/skills/respond-to-pr-comments/SKILL.md`
Expected: No issues

#### Step 8: Verify skill is under 500 lines

Run: `wc -l fzymgc-house/skills/respond-to-pr-comments/SKILL.md`
Expected: Under 500 lines

#### Step 9: Commit

```text
git add fzymgc-house/skills/respond-to-pr-comments/SKILL.md
git commit -m "feat(respond-to-pr-comments): integrate beads for review state persistence"
```

---

### Task 6: Update CLAUDE.md skill descriptions

Update the Available Skills section in `CLAUDE.md` to mention beads integration.

**Files:**

- Modify: `CLAUDE.md`

#### Step 1: Update review-pr description

Change the `review-pr` bullet to mention beads:

```markdown
- **review-pr** - Comprehensive PR review using 9 specialized subagents (code quality, error handling, test coverage,
  type design, comments, security, API compatibility, spec compliance, code simplification).
  Findings persisted as beads for cross-session context. User-invoked via `/review-pr [aspects]`.
```

#### Step 2: Update respond-to-pr-comments description

Change the `respond-to-pr-comments` bullet to mention beads:

```markdown
- **respond-to-pr-comments** - GitHub PR review comment management (list, acknowledge, respond to feedback, full
  review-response workflows). Reads review findings from beads for context-aware responses.
```

#### Step 3: Verify markdown lint passes

Run: `rumdl check CLAUDE.md`
Expected: No issues

#### Step 4: Commit

```text
git add CLAUDE.md
git commit -m "docs: update skill descriptions to reflect beads integration"
```

---

### Task 7: Final verification and cleanup

Cross-check all changes against the design doc.

**Files:**

- Read: `docs/plans/2026-02-15-beads-review-integration-design.md`

#### Step 1: Verify no JSONL/REVIEW_DIR references remain anywhere

Run: `grep -r "JSONL\|jsonl\|REVIEW_DIR\|mktemp" fzymgc-house/skills/review-pr/ fzymgc-house/skills/respond-to-pr-comments/`
Expected: No matches

#### Step 2: Verify all agent files have Bead Output section

Run: `grep -l "## Bead Output" fzymgc-house/skills/review-pr/references/agent-*.md | wc -l`
Expected: 9

#### Step 3: Verify bd CLI in both skills' allowed-tools

Run: `grep "bd create" fzymgc-house/skills/review-pr/SKILL.md fzymgc-house/skills/respond-to-pr-comments/SKILL.md`
Expected: 2 matches (one per skill)

#### Step 4: Run skill-qa validation (optional)

If the `skill-qa` skill is available, run it against both skills to validate
SKILL.md best practices (under 500 lines, proper frontmatter, etc.).

#### Step 5: Commit any fixes

If any issues found, fix and commit:

```text
git commit -m "fix(skills): address skill-qa findings from beads integration"
```
