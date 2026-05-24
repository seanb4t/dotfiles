#!/usr/bin/env fish

# Managed by chezmoi. Restores Claude Code plugin marketplaces + plugins.
# Mirror of the skills.sh restore — this half covers PLUGINS (commands/agents/hooks/MCP).
# Regenerated from denver state. Edit lists below; run_onchange re-runs on change.
#
# Marketplace name <- source repo:
#   beads-marketplace            steveyegge/beads
#   claude-code-workflows        wshobson/agents
#   claude-plugins-official      anthropics/claude-plugins-official
#   fzymgc-house-skills          fzymgc-house/fzymgc-house-skills
#   superpowers-marketplace      obra/superpowers-marketplace

if not command -q claude
    echo "claude not found; installing..."; curl -fsSL claude.ai/install.sh | bash
end

set -l marketplaces \
    steveyegge/beads \
    wshobson/agents \
    anthropics/claude-plugins-official \
    fzymgc-house/fzymgc-house-skills \
    obra/superpowers-marketplace
for repo in $marketplaces
    echo "marketplace add: $repo"; claude plugin marketplace add $repo 2>/dev/null; or true
end
claude plugin marketplace update 2>/dev/null; or true

set -l plugins \
    beads@beads-marketplace \
    c4-architecture@claude-code-workflows \
    chrome-devtools-mcp@claude-plugins-official \
    cicd-automation@claude-code-workflows \
    claude-md-management@claude-plugins-official \
    code-documentation@claude-code-workflows \
    code-refactoring@claude-code-workflows \
    code-simplifier@claude-plugins-official \
    codebase-cleanup@claude-code-workflows \
    commit-commands@claude-plugins-official \
    comprehensive-review@claude-code-workflows \
    context-management@claude-code-workflows \
    context7@claude-plugins-official \
    debugging-toolkit@claude-code-workflows \
    dev-flow@fzymgc-house-skills \
    documentation-generation@claude-code-workflows \
    double-shot-latte@superpowers-marketplace \
    error-debugging@claude-code-workflows \
    error-diagnostics@claude-code-workflows \
    explanatory-output-style@claude-plugins-official \
    gopls-lsp@claude-plugins-official \
    jj@fzymgc-house-skills \
    jvm-languages@claude-code-workflows \
    kubernetes-operations@claude-code-workflows \
    learning-output-style@claude-plugins-official \
    observability-monitoring@claude-code-workflows \
    playwright@claude-plugins-official \
    plugin-dev@claude-plugins-official \
    pr-review-toolkit@claude-plugins-official \
    pr-review@fzymgc-house-skills \
    python-development@claude-code-workflows \
    ralph-loop@claude-plugins-official \
    security-guidance@claude-plugins-official \
    shell-scripting@claude-code-workflows \
    systems-programming@claude-code-workflows
for plugin in $plugins
    echo "install: $plugin"; claude plugin install $plugin --scope user 2>/dev/null; or echo "  (failed/already): $plugin"
end

echo "Plugin restore complete: 5 marketplaces, 35 plugins."
