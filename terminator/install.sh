#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

[ "$(uname -s)" = "Darwin" ] && exit 0
test -z "$KEEP_TERMINATOR" || exit 0
mkdir -p ~/.config/terminator/
ln -sf "$DOTFILES"/terminator/config ~/.config/terminator/config
