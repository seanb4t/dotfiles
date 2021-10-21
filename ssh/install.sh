#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

test -L ~/.ssh/config || {
	mv ~/.ssh/config ~/.ssh/config.local
	ln -s "$DOTFILES"/ssh/config ~/.ssh/config
}
test -f ~/.ssh/config.local || touch ~/.ssh/config.local
