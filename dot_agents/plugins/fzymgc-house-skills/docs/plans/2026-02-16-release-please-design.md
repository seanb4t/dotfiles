# Release Please Integration — Design

**Date:** 2026-02-16
**Status:** Approved
**Scope:** Automated versioning and changelog via release-please

## Problem

Versions in `marketplace.json`, `plugin.json`, and individual SKILL.md
`metadata.version` fields are bumped manually. This is error-prone —
PR #10 almost shipped without a version bump. The repo already enforces
conventional commits via cog, which is exactly what release-please
consumes.

## Solution

Integrate [release-please](https://github.com/googleapis/release-please)
as a GitHub Action using manifest mode. One root package manages the
plugin-level version; one package per skill manages skill-level versions.
A drift-detection CI check ensures the config stays in sync with actual
skill directories.

## Architecture: Flat Manifest

### Packages

| Package path | Tracks | Extra-files |
|---|---|---|
| `.` (root) | Plugin version | `marketplace.json`, `plugin.json` |
| `fzymgc-house/skills/grafana` | grafana skill | `SKILL.md` |
| `fzymgc-house/skills/terraform` | terraform skill | `SKILL.md` |
| `fzymgc-house/skills/review-pr` | review-pr skill | `SKILL.md` |
| `fzymgc-house/skills/respond-to-pr-comments` | respond-to-pr-comments | `SKILL.md` |
| `fzymgc-house/skills/address-review-findings` | address-review-findings | `SKILL.md` |
| `fzymgc-house/skills/skill-qa` | skill-qa skill | `SKILL.md` |

release-please detects which paths were touched by conventional commits
and only bumps those packages. A combined Release PR accumulates
changes until merged.

### Version Files Updated

**JSON files** — native `jsonpath` updater:

- `.claude-plugin/marketplace.json` → `$.version`
- `fzymgc-house/plugin.json` → `$.version`

**SKILL.md files** — `generic` updater with marker comment:

```yaml
metadata:
  version: 0.4.0 # x-release-please-version
```

The `# x-release-please-version` marker is a YAML comment that tells
the generic updater which line to modify. It does not affect frontmatter
parsing.

### Skills Missing metadata.version

Three skills currently lack `metadata.version` in their frontmatter
and need it added: `grafana`, `terraform`, `skill-qa`. All start at
`0.1.0`.

## Configuration Files

### release-please-config.json

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "packages": {
    ".": {
      "release-type": "simple",
      "package-name": "fzymgc-house-skills",
      "extra-files": [
        {
          "type": "json",
          "path": ".claude-plugin/marketplace.json",
          "jsonpath": "$.version"
        },
        {
          "type": "json",
          "path": "fzymgc-house/plugin.json",
          "jsonpath": "$.version"
        }
      ]
    },
    "fzymgc-house/skills/grafana": {
      "release-type": "simple",
      "package-name": "grafana",
      "extra-files": [
        {
          "type": "generic",
          "path": "fzymgc-house/skills/grafana/SKILL.md"
        }
      ]
    },
    "fzymgc-house/skills/terraform": {
      "release-type": "simple",
      "package-name": "terraform",
      "extra-files": [
        {
          "type": "generic",
          "path": "fzymgc-house/skills/terraform/SKILL.md"
        }
      ]
    },
    "fzymgc-house/skills/review-pr": {
      "release-type": "simple",
      "package-name": "review-pr",
      "extra-files": [
        {
          "type": "generic",
          "path": "fzymgc-house/skills/review-pr/SKILL.md"
        }
      ]
    },
    "fzymgc-house/skills/respond-to-pr-comments": {
      "release-type": "simple",
      "package-name": "respond-to-pr-comments",
      "extra-files": [
        {
          "type": "generic",
          "path": "fzymgc-house/skills/respond-to-pr-comments/SKILL.md"
        }
      ]
    },
    "fzymgc-house/skills/address-review-findings": {
      "release-type": "simple",
      "package-name": "address-review-findings",
      "extra-files": [
        {
          "type": "generic",
          "path": "fzymgc-house/skills/address-review-findings/SKILL.md"
        }
      ]
    },
    "fzymgc-house/skills/skill-qa": {
      "release-type": "simple",
      "package-name": "skill-qa",
      "extra-files": [
        {
          "type": "generic",
          "path": "fzymgc-house/skills/skill-qa/SKILL.md"
        }
      ]
    }
  }
}
```

### .release-please-manifest.json

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

## GitHub Actions Workflows

### Release Please Workflow

```yaml
# .github/workflows/release-please.yml
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

### PR Check Workflow

```yaml
# .github/workflows/check-skills.yml
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

## CLAUDE.md Changes

Add to the Gotchas section:

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

## Runtime Flow

1. Merge a PR with conventional commits (already enforced by cog)
2. release-please parses commits, determines which packages were touched
3. Opens/updates a "Release PR" with version bumps + CHANGELOG updates
4. Merge the Release PR when ready → creates GitHub Releases per
   bumped component

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| release-type | `simple` | No package.json/Cargo.toml to manage |
| Manifest mode | Yes | Independent per-skill versioning |
| SKILL.md updater | `generic` with marker | Native release-please pattern |
| Separate PRs | No (combined) | Simpler to manage for small repo |
| Drift detection | CI check | Catches missing config on every PR |
| Lint in CI | Yes | No CI exists currently |
