#!/usr/bin/env fish

# This script tis run after the installation of the dotfiles
# to install claude code.

# Install claude code if it is not already installed in ~/.local/bin/claude

if not test -f ~/.local/bin/claude; then
    echo "Installing claude code..."
    curl -fsSL claude.ai/install.sh | bash
end
