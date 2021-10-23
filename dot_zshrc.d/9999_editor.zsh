
#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

if command -v code > /dev/null 2>&1; then
    export EDITOR="code -w"
    export GIT_EDITOR="code -w"
fi

export VISUAL=vim
