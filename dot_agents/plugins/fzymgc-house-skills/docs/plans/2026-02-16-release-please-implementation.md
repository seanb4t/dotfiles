# Release Please Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automate version bumping and changelog generation using
release-please with manifest mode.

**Architecture:** release-please GitHub Action in manifest mode with
one root package (plugin version) and one package per skill (skill
versions). Drift detection CI check ensures config stays in sync
with skill directories.

**Tech Stack:** GitHub Actions, release-please v4, jq (for CI check)

**Design doc:** `docs/plans/2026-02-16-release-please-design.md`

---

## Task 1: Add metadata.version to skills missing it

**Files:**

- Modify: `fzymgc-house/skills/grafana/SKILL.md` (line 17, before closing `---`)
- Modify: `fzymgc-house/skills/terraform/SKILL.md` (line 16, before closing `---`)
- Modify: `fzymgc-house/skills/skill-qa/SKILL.md` (line 13, before closing `---`)

### Step 1: Add metadata block to grafana/SKILL.md

Insert before the closing `---` on line 17:

```yaml
metadata:
  author: fzymgc-house
  version: 0.1.0
```

### Step 2: Add metadata block to terraform/SKILL.md

Insert before the closing `---` on line 16:

```yaml
metadata:
  author: fzymgc-house
  version: 0.1.0
```

### Step 3: Add metadata block to skill-qa/SKILL.md

Insert before the closing `---` on line 13:

```yaml
metadata:
  author: fzymgc-house
  version: 0.1.0
```

### Step 4: Verify all skills have metadata.version

Run: `grep -r "version:" fzymgc-house/skills/*/SKILL.md`
Expected: All 6 skills show a version line.

### Step 5: Commit

```text
feat(skills): add metadata.version to grafana, terraform, skill-qa
```

---

## Task 2: Add x-release-please-version markers to all SKILL.md files

**Files:**

- Modify: `fzymgc-house/skills/grafana/SKILL.md`
- Modify: `fzymgc-house/skills/terraform/SKILL.md`
- Modify: `fzymgc-house/skills/skill-qa/SKILL.md`
- Modify: `fzymgc-house/skills/review-pr/SKILL.md`
- Modify: `fzymgc-house/skills/respond-to-pr-comments/SKILL.md`
- Modify: `fzymgc-house/skills/address-review-findings/SKILL.md`

### Step 1: Add marker comment to each version line

For each SKILL.md, change:

```yaml
  version: X.Y.Z
```

to:

```yaml
  version: X.Y.Z # x-release-please-version
```

Preserve the existing version number in each file:

| Skill | Current version |
|-------|-----------------|
| grafana | 0.1.0 (from Task 1) |
| terraform | 0.1.0 (from Task 1) |
| skill-qa | 0.1.0 (from Task 1) |
| review-pr | 0.3.0 |
| respond-to-pr-comments | 0.4.0 |
| address-review-findings | 0.1.0 |

### Step 2: Verify markers

Run: `grep -r "x-release-please-version" fzymgc-house/skills/*/SKILL.md`
Expected: 6 lines, one per skill.

### Step 3: Commit

```text
chore(skills): add x-release-please-version markers to SKILL.md files
```

---

## Task 3: Create release-please configuration files

**Files:**

- Create: `release-please-config.json`
- Create: `.release-please-manifest.json`

### Step 1: Create release-please-config.json

Copy the exact JSON from the design doc "release-please-config.json"
section. Ensure the `$schema` field is present at the top.

### Step 2: Create .release-please-manifest.json

```json
{
  ".": "0.5.0",
  "fzymgc-house/skills/grafana": "0.1.0",
  "fzymgc-house/skills/terraform": "0.1.0",
  "fzymgc-house/skills/review-pr": "0.3.0",
  "fzymgc-house/skills/respond-to-pr-comments": "0.4.0",
  "fzymgc-house/skills/address-review-findings": "0.1.0",
  "fzymgc-house/skills/skill-qa": "0.1.0"
}
```

### Step 3: Verify JSON is valid

Run: `jq . release-please-config.json > /dev/null && echo OK`
Run: `jq . .release-please-manifest.json > /dev/null && echo OK`
Expected: Both print OK.

### Step 4: Commit

```text
feat(ci): add release-please config and manifest
```

---

## Task 4: Create GitHub Actions workflows

**Files:**

- Create: `.github/workflows/release-please.yml`
- Create: `.github/workflows/check-skills.yml`

### Step 1: Create .github/workflows directory

Run: `mkdir -p .github/workflows`

### Step 2: Create release-please.yml

```yaml
name: Release Please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          manifest-file: .release-please-manifest.json
          config-file: release-please-config.json
```

### Step 3: Create check-skills.yml

```yaml
name: Check Skills

on:
  pull_request:
    branches: [main]

jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check release-please config covers all skills
        run: |
          actual=$(find fzymgc-house/skills -name SKILL.md -exec dirname {} \; | sort)
          configured=$(jq -r '.packages | keys[] | select(. != ".")' release-please-config.json | sort)
          if ! diff <(echo "$actual") <(echo "$configured"); then
            echo "::error::Skill directories and release-please-config.json are out of sync"
            exit 1
          fi

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install rumdl
        run: cargo install rumdl
      - name: Lint markdown
        run: rumdl check fzymgc-house/skills/*/SKILL.md
```

### Step 4: Verify YAML is valid

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release-please.yml'))" && echo OK`
Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/check-skills.yml'))" && echo OK`
Expected: Both print OK.

### Step 5: Commit

```text
feat(ci): add release-please and check-skills GitHub Actions workflows
```

---

## Task 5: Update CLAUDE.md

**Files:**

- Modify: `CLAUDE.md`

### Step 1: Add Release Versioning section

Add the following after the "### Linting" section (after line ~107):

```markdown
### Release Versioning

Versions are managed by release-please. Do NOT manually bump versions
in `marketplace.json`, `plugin.json`, or SKILL.md `metadata.version`
fields.

When adding or removing a skill, update both:

- `release-please-config.json` (add/remove package entry)
- `.release-please-manifest.json` (add/remove version entry)

CI will fail if skill directories and release-please config fall out
of sync.
```

### Step 2: Verify

Run: `grep "release-please" CLAUDE.md`
Expected: Multiple matches in the new section.

### Step 3: Commit

```text
docs: add release versioning guidance to CLAUDE.md
```

---

## Task 6: Validate everything

### Step 1: Verify all 6 skills have versioned metadata with markers

Run: `grep -r "x-release-please-version" fzymgc-house/skills/*/SKILL.md | wc -l`
Expected: 6

### Step 2: Verify manifest versions match SKILL.md versions

Run: `jq -r 'to_entries[] | select(.key != ".") | "\(.key): \(.value)"' .release-please-manifest.json`

Cross-reference with:

Run: `grep -r "version:" fzymgc-house/skills/*/SKILL.md | grep "x-release-please"`

Expected: Versions match between manifest and SKILL.md for each skill.

### Step 3: Verify drift check would pass

```bash
diff \
  <(find fzymgc-house/skills -name SKILL.md -exec dirname {} \; | sort) \
  <(jq -r '.packages | keys[] | select(. != ".")' \
    release-please-config.json | sort)
```

Expected: No output (no diff).

### Step 4: Run linters on modified files

Run: `rumdl check fzymgc-house/skills/*/SKILL.md`
Run: `rumdl check CLAUDE.md`
Expected: No errors.

### Step 5: Commit any fixes if needed

```text
fix(ci): lint fixes for release-please integration
```
