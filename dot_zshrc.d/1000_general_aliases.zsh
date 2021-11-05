#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

function has() {
  command -v $1 > /dev/null 2>&1
}

#
## cat/bat
#
has bat && alias cat=bat && alias catp='bat -pp'

#
## grep/ack/rg
#
has rg && alias grep=rg && alias ack=rg

#
## exa / ls
#
if has exa; then
  alias ls='exa -F --group-directories-first'
  alias l='exa -lbF --group-directories-first'
  alias ll='exa -lbGF --git --group-directories-first'
  alias llm='exa -lbGd --git --sort=modified'                            # long list, modified date sort
  alias la='exa -lbhHigUmuSa --time-style=long-iso --git --color-scale'  # all list
  alias lg='exa -TF'
  alias lx='exa -lbhHigUmuSa@ --time-style=long-iso --git --color-scale' # all + extended list
  alias lS='exa -1'                                                              # one column, just names
fi

#
## top/htop
#
has htop && alias top=htop
