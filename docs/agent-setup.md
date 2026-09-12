# Shared Claude and Codex setup

This repository manages the portable user configuration for both agents. Root
`AGENTS.md` contains repository guidance, and root `CLAUDE.md` imports it. Both
remain excluded from home-directory deployment.

## Ownership

| Content | Source and owner |
| --- | --- |
| Shared user preferences | `.chezmoitemplates/user-preferences.md.tmpl`, rendered for both agents |
| Claude global instructions | `dot_claude/modify_CLAUDE.md`; preserves installer additions and replaces only known/marked preference content |
| Claude settings | `dot_claude/modify_settings.json`; portable preferences merge around native hooks and status-line state |
| Shared DevOps reviewer | `.chezmoitemplates/devops-reviewer.md`, rendered into native Claude and Codex agent definitions |
| Codex global instructions | `dot_codex/modify_AGENTS.md`; replaces only the marked preference block and preserves installer additions |
| Codex settings | `dot_codex/modify_private_config.toml`; merges portable preferences, preserving unknown app/user/installer state |
| Direct MCP definitions | `.chezmoitemplates/codex-mcp.json.tmpl` |
| MCP credentials | `.chezmoitemplates/mcp-secrets.json.age`, encrypted with the existing chezmoi age recipient |
| Standalone non-GSD skills | `npx skills`; selection and sources in `agent-skills.json` |
| Personal or locally preserved skill sources | `agent-skill-sources/`, installed through `npx skills` |
| GSD skills, adapters, agents, workflows, hooks | **GSD only**; neither chezmoi nor the skills restorer owns the installed files |
| Native plugin components and bundled skills | Their native plugin installers; do not duplicate them into the standalone skill selection |
| Boost hooks and `BOOST.md` | Boost's native installer |
| Orca/Herdr integrations | Their native installers; machine-specific runtime registrations are preserved |

The previous encrypted whole-file Codex snapshot has been replaced by the merge
template. The original encrypted snapshot remains recoverable from the migration backup. The merge retains project trust, app paths, plugin state,
hook approvals, notification commands, and custom MCP servers. Owned server
definitions are replaced as whole objects, so switching Firecrawl from STDIO to
HTTP does not leave incompatible command fields behind.

Credentials are never included in diagnostic output. Reuse the existing
1Password/age setup when changing the encrypted credential map. OAuth sessions
and agent login caches remain native-client state and are not committed.

## Apply and verify

Apply the configuration without invoking unrelated lifecycle scripts:

```sh
chezmoi apply --exclude=scripts \
  ~/.codex/config.toml ~/.codex/AGENTS.md \
  ~/.codex/rules/agent-policy.rules ~/.claude/CLAUDE.md ~/.claude/settings.json \
  ~/.codex/agents/devops-code-reviewer.toml ~/.claude/agents/devops-code-reviewer.md
python3 scripts/agent-skills.py audit
python3 scripts/agent-skills.py restore
python3 scripts/restore-claude-plugins.py --dry-run
uv run scripts/check-agent-setup.py
uv run scripts/check-agent-setup.py --live-mcp
python3 -m unittest discover -s tests -p 'test_*.py'
```

The live check uses Codex app-server tool discovery, including stored OAuth
and STDIO transports; it never starts a model turn or invokes a tool. Effective
instruction loading also needs a fresh Codex client. `codex mcp list` verifies registration, not connectivity.
Avoid dumping its JSON output or a full config diff into logs: these may contain
credentials. Configuration changes take effect in new/restarted clients.

Ordinary chezmoi application runs the selection-based skill restore and native
plugin restore scripts. They do not run a general skill/plugin update. Restore
failures are surfaced rather than hidden behind `or true`.

## Skill installation and updates

`~/.agents/skills/<name>` is canonical. Codex reads it directly; Claude uses
`~/.claude/skills/<name>` symlinks. The restorer uses the pinned Skills CLI for
missing installs, repairs links for already installed skills, and removes only
known redundant/broken legacy Codex aliases after a canonical replacement exists.
Different local contents stop that skill's migration. Identical standalone
copies replaced by links are backed up under
`~/.local/state/agent-setup/skill-backups/`.

The migration selection contains 62 standalone non-GSD skills: 48 pinned remote
sources and 14 local sources. Local sources preserve authored content or content
whose upstream provenance was not recorded. They are real sources, not a second
deployed copy. The old `dot_agents/skills`, `dot_claude/skills`, and managed global
lock snapshot have been retired. GSD files in those old source snapshots were
removed from chezmoi ownership; the live GSD files were not rewritten.

Native ownership review removed eight bundled skills from the standalone
selection. Homelab owns `terraform` and `skill-qa` through native Claude and Codex
plugins. Grafana was subsequently removed at the user's request. Engram owns its five memory skills through its native
Claude plugin; Codex discovers links under `~/.agents/skills` pointing to that
plugin's stable marketplace source directory. The Claude plugin restorer creates
those links after installing the native marketplace. Updating that native source
is immediately visible through the links; `npx skills` never updates them.
The manifest rejects plugin-owned names in its standalone selection.

The previous standalone versions and local sources were preserved under
`~/.local/state/agent-setup/skill-backups/native-plugin-ownership-0se_v2zb/`.
An older Codex-only `gh-stack` 0.0.9 copy was also backed up, leaving the existing
shared 0.1.0 copy authoritative. The audit now reports physical Codex copies as
conflicts, and restore checks both agents before installing a missing canonical
skill. Alternate-home restore is rejected before any link changes.

The global `~/.agents/.skill-lock.json` belongs to the Skills CLI. Its timestamps,
selection preferences, and installation metadata are not a dotfile restore
manifest. `experimental_install` restores project lockfiles and is not used to
reconstruct the global installation.

To add a standalone skill, use an explicit selection:

```sh
npx skills add owner/repo --global --skill example --agent claude-code codex --yes
```

Then record the selection and a reviewed source revision in `agent-skills.json`.
For updates, use an explicit named `npx skills update example --global` operation
and update the restore source revision as appropriate. Avoid bulk updates that
include GSD. Existing skill contents are intentionally preserved during restore;
they can predate the manifest's pinned upstream revision. A missing installation
uses the recorded revision. Local skills are refreshed by reinstalling their
authored source with `npx skills add ./agent-skill-sources/<name> ...`.

The `gsd-` prefix is rejected by the manifest loader. GSD's Claude and Codex
adapters differ; do not replace either with symlinks to the other. Invoke GSD's
own installer/update workflow when its runtime needs restoration or an update.
The inspected installs were Claude 1.13.0 and Codex 1.10.0; this migration does
not upgrade either one.

## Native integrations

The Codex plugin restore uses the existing `fzymgc-house-skills` marketplace to
install `homelab`, `pr-review`, `jj`, and `superpowers`. The marketplace and source
plugins are managed under `dot_agents/plugins/`. Codex manifests are rendered
into the real source plugin directories, keeping one source skill tree. The
earlier thin wrappers used symlinks that native installation skipped, leaving
empty skill caches despite reporting successful installation. Native reinstall
from the real directories now packages 21 skills. On a new machine, apply those
paths before invoking the Codex plugin restore. App-bundled marketplaces
and plugins remain app-managed.
The restorer preserves explicitly disabled Codex plugins.

Claude installs `homelab@local-agent-plugins` from the managed local marketplace
at `~/.agents/plugins/.claude-plugin/marketplace.json`, using the same Homelab
source as Codex. Its only skills are Terraform and skill QA; its MCP definitions
contain Context7 and Terraform. The old Claude upstream Homelab installation was
uninstalled. Local marketplace paths are expanded to the current user's home
when settings are rendered. This keeps native restores from reintroducing Grafana.
Grafana skill sources were backed up under
`~/.local/state/agent-setup/skill-backups/removed-grafana-wcppkyaa/`.

Claude plugin restoration derives marketplaces and selections from the current
`settings.json` rather than an out-of-date second hardcoded list. It installs
missing user-scope plugins and restores a disabled selection after installation.
Existing installs are not bulk-updated. Plugin names are not evidence that their
Claude and Codex implementations expose identical agents, hooks, or commands.

For missing Boost integrations, the native command is
`boost init --codex --claude --no-boostgraph`; its own installer handles hook
files and guidance. Review any installer terms or hook trust prompts through
that native flow. Do not copy another machine's hook approval hashes.

## Capability parity and limits

| Area | Result / remaining difference |
| --- | --- |
| Repository and personal guidance | Shared source, with native instruction entry points and installer content preserved |
| Personal DevOps review agent | Shared review instructions, with a native definition for each agent |
| Direct MCP definitions | All 14 Claude definitions represented; Codex-specific definitions preserved |
| Standalone skills | 62 selected standalone skills shared; plugin-owned skills excluded and legacy Codex copies reconciled |
| GSD | Native owner preserved; installed versions and runtime-specific behavior still differ |
| Homelab / PR review / jj / superpowers | 21 bundled skills packaged and installed; Terraform and skill QA retained, Grafana removed; full workflows remain untested |
| Engram | Native plugin memory skills shared through links; OAuth connection verified with 15 tools |
| Context7 | Shared CLI guidance and MCP definition; live tool discovery passes |
| CodeGraph | Global definition retained; disabled in this unindexed repo through `.codex/config.toml`, following the opt-in indexing rule |
| Browser / Playwright / Chrome tools | Codex has native browser integrations; Claude plugin commands are not copied |
| Claude code, language, documentation, infrastructure, and review plugin agents | Remain native Claude plugin capabilities; no claim that all named agents or commands are ported |
| Ralph loop, learning/explanatory styles, security-guidance, Warp, tmux, grepping, tldraw | Claude-specific plugin behavior remains native; no identical Codex hook behavior asserted |
| Notifications | Existing Codex app/terminal integration preserved; Claude's tmux terminal-sequence mechanism is different |
| Direct command permissions | Native Codex rules cover the selected `gh pr merge`, Terraform, Kubernetes deletion, and `rm -rf` prefixes |
| File-pattern permissions and custom merge guard | Claude semantics are not reproduced by those prefix rules; retain the native sandbox and treat this as a policy gap |

As observed on 2026-09-12, native Codex tool discovery passed for
clickhouse_ro, clickhouse_rw, clickstack, context7, deepwiki, engram, exa, fal,
firecrawl, firewalla_ro, karakeep, and kubernetes (13 tools after successful OAuth
login). After the user's Sentry login, fresh native discovery also exposed 7
`sentry-holomush` tools. The full setup checker now passes with no outstanding
authentication failures among the enabled direct servers.
A raw-header HTTP check initially reported an Engram 401,
but it omitted Codex's stored OAuth credentials; native discovery and an Engram
read confirmed the working connection. Use the native checker for accurate
OAuth status.

Kubernetes scopes are explicitly pinned to `mcp-kubernetes groups offline_access`,
matching Claude's working OAuth grant. A local registration capture using the
installed Codex CLI and equivalent discovery metadata showed that an unscoped
login requested the identity provider's entire advertised scope list. The live
login was rejected by Keycloak's "Allowed Client Scopes" registration policy.
Explicit scopes restricted the captured registration to the three intended
scopes. The user's subsequent live login succeeded with
`codex mcp login kubernetes --scopes mcp-kubernetes,groups,offline_access`,
confirming the registration fix. Fresh native Codex discovery then exposed 13
Kubernetes tools. A fresh read-only Codex session then successfully called
`namespaces_list` and returned 51 namespaces, verifying real cluster access.

A fresh Codex session also completed a Sentry project-scoped issue search,
returning zero unresolved issues with a limit of one. Identity and organization
listing were unavailable on this scoped endpoint. The noninteractive smoke test
needed a one-invocation Sentry tool approval override; no persistent approval
policy was changed.

The installed CodeGraph server timed out during handshake in this unindexed
repository. The project override disables it here, while the global definition
remains available for indexed projects. Remove that override only when the user
chooses to index the repository; indexing is not part of this migration.

The source checks validated the original 70 sources; the retained 62 are a subset, and a clean temporary
project install validated the pinned upstream install and Claude symlink layout.
A fresh read-only Codex session identified the shared preferences, this chezmoi
repository, GSD ownership, and the shared find-docs/agent-browser skills. A separate Codex session discovered
the native DevOps reviewer, and a fresh Claude session confirmed the shared
preferences, AGENTS.md import, and GSD ownership. A Claude session with the Skill
tool enabled also confirmed find-docs and agent-browser in its catalog. Unit
checks cover preservation of app/installer config, transport replacement,
idempotence, and protection of local skill changes. Native permission-rule
checks validate the five selected command cases.

This is a working shared configuration and restore path, with explicit remaining
native-plugin/policy gaps and workflow validation still needed. Tool discovery alone is not full
behavioral parity.

The direct review fixed empty native plugin skill caches, eight skills with
conflicting ownership, an older separate Codex `gh-stack` copy, and restore
preflight gaps. Twenty-one regression tests pass. Fresh Codex reads loaded GSD help,
Homelab Grafana (before its removal), and PR-review skill entries. Their full workflows were not run;
some upstream entries still use Claude-oriented plugin-root variables or
ambiguous relative references, which need workflow-specific validation. No
CodeRabbit review was run.

The local migration backup is at `~/.local/state/agent-setup/codex-parity-backup-20260912/`.
Beads was left untouched under the user-authorized tracking exception. Git LFS hooks are retained when committing and pushing; the user-authorized
Beads exception also excludes Beads Git hook operations.
