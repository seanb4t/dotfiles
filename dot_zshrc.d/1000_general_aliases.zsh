#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

function has() {
  command -v $1 > /dev/null 2>&1
}

has bat && alias cat=bat
has rg && alias grep=rg && alias ack=rg
has fd && alias find=fd
