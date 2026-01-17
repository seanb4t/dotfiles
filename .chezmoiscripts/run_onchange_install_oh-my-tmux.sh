#!/usr/bin/env bash
set -euo pipefail

# Install or update oh-my-tmux
if [ -d ~/.tmux/.git ] && [ -f ~/.tmux/.tmux.conf ]; then
  echo "Updating oh-my-tmux..."
  cd ~/.tmux && git pull
else
  echo "Installing oh-my-tmux..."
  git clone https://github.com/gpakosz/.tmux.git ~/.tmux
  ln -s -f ~/.tmux/.tmux.conf ~/.tmux.conf
fi
echo "oh-my-tmux ready"

