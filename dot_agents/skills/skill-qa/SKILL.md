---
name: skill-qa
description: >-
  Validates SKILL.md files against Claude Code skill best practices.
  Checks conciseness, description quality, progressive disclosure,
  workflow structure, and common anti-patterns. Use when reviewing
  or auditing skills before shipping.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
metadata:
  author: fzymgc-house
  version: 0.1.0 # x-release-please-version
---

# Skill QA Review

Run this checklist against the target SKILL.md. Report pass/fail
for each item with a one-line explanation for failures.

## Checklist

### Metadata

- [ ] `name`: lowercase, hyphens only, max 64 chars, no reserved words
- [ ] `description`: non-empty, max 1024 chars, third person, includes
  both what and when
- [ ] `description` includes specific trigger phrases users would say

### Conciseness

- [ ] SKILL.md body is under 500 lines
- [ ] No explanations of concepts Claude already knows
- [ ] No verbose preambles or background sections
- [ ] Each paragraph justifies its token cost

### Structure

- [ ] Reference files are one level deep (no nested chains)
- [ ] Files over 100 lines have a table of contents
- [ ] Progressive disclosure used (details in separate files)
- [ ] Conditional workflows use clear decision points

### Workflows

- [ ] Complex tasks have numbered steps
- [ ] Multi-step workflows include a copy-paste checklist
- [ ] Feedback loops exist for quality-critical operations
- [ ] Steps that must not be combined are explicitly marked

### Scripts

- [ ] Execute vs read intent is clear for each script
- [ ] Scripts handle errors (don't punt to Claude)
- [ ] No magic constants without justification
- [ ] Required packages are listed

### Anti-patterns

- [ ] No Windows-style paths
- [ ] No time-sensitive information
- [ ] Consistent terminology throughout
- [ ] No multiple equivalent options without a default
- [ ] No deeply nested file references
