#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

if command -v vim >/dev/null 2>&1; then
  echo > /dev/null
elif command -v brew >/dev/null 2>&1; then
  brew install neovim
elif command -v yay >/dev/null 2>&1; then
  yay -Sy --needed --noprovides --noconfirm neovim neovim-drop-in
else
  echo "Unable to install/find vim!"
  exit 1
fi

nvim +'PlugInstall --sync' +qa
nvim +'PlugUpdate' +qa
