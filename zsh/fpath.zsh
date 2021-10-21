#!/bin/zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

#add each topic folder to fpath so that they can add functions and completion scripts
for topic_folder in $DOTFILES/*; do
	if [ -d "$topic_folder" ]; then
		fpath=($topic_folder $fpath)
	fi
done

[[ -d "${HOME}/.zsh_custom/functions" ]] && fpath=("${HOME}/.zsh_custom/functions" $fpath)
