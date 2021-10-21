# your default editor
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

code="code"
if command -v code-insiders >/dev/null 2>&1; then
  code="code-insiders"
fi
export EDITOR="vim"
export VISUAL="$(command -v ${code}) -nw"
export VEDITOR="$(command -v ${code}) -nw"
