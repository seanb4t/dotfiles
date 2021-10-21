#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

if command -v bfs >/dev/null 2>&1; then
    echo > /dev/null
elif command -v brew >/dev/null 2>&1; then
    HOMEBREW_NO_AUTO_UPDATE=1 brew install tavianator/tap/bfs
elif command -v yay >/dev/null 2>&1; then
    yay -Sy --needed --noprovides --noconfirm bfs
fi
