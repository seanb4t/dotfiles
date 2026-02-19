#!/bin/bash
# Install TPM (Tmux Plugin Manager)

[[ -d "$HOME/.config/tmux/plugins" ]] || mkdir -p "$HOME/.config/tmux/plugins"

TPM_DIR="$HOME/.config/tmux/plugins/tpm"

if [ ! -d "$TPM_DIR" ]; then
    echo "Installing TPM..."
    git clone https://github.com/tmux-plugins/tpm "$TPM_DIR"
else
    echo "Updating TPM..."
    cd "$TPM_DIR" && git pull
fi

# Install/update TPM plugins headlessly
if [ -x "$TPM_DIR/bin/install_plugins" ]; then
    echo "Installing TPM plugins..."
    TMUX_PLUGIN_MANAGER_PATH="$HOME/.config/tmux/plugins" "$TPM_DIR/bin/install_plugins"
fi
