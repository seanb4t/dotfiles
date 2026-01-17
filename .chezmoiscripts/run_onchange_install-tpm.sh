#!/bin/bash
# Install TPM (Tmux Plugin Manager)

TPM_DIR="$HOME/.tmux/plugins/tpm"

if [ ! -d "$TPM_DIR" ]; then
    echo "Installing TPM..."
    git clone https://github.com/tmux-plugins/tpm "$TPM_DIR"
else
    echo "Updating TPM..."
    cd "$TPM_DIR" && git pull
fi
