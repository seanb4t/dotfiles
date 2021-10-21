#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

if command -v fzf >/dev/null 2>&1; then
  echo > /dev/null
elif command -v brew >/dev/null 2>&1; then
  HOMEBREW_NO_AUTO_UPDATE=1 brew install fzf
elif command -v yay >/dev/null 2>&1; then
  yay -Sy --needed --noprovides --noconfirm fzf
else
  echo "Unable to install fzf"
fi

# vim: set ft=sh sw=2 ts=2 et:
