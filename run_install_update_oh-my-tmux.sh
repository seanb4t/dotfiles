#!/usr/bin/env bash

# Install or update oh-my-tmux
if [ -d ~/.tmux/.git ] && [ -f ~/.tmux/.tmux.conf ]; then
  cd ~/.tmux && git pull -q
else
  cd ~ && git clone https://github.com/gpakosz/.tmux.git
  cd ~ && ln -s -f .tmux/.tmux.conf .
fi

