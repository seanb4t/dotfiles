#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2



export DONT_PRINT_SSH_KEY_LIST=1
export QUICKSTART_KIT_REFRESH_IN_DAYS=7

[[ -d /home/linuxbrew ]] && export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
[[ -d /opt/homebrew ]] && export PATH="/opt/homebrew/bin:$PATH"

#
## Update brew every day
#
export HOMEBREW_AUTO_UPDATE_SECS=86400

#
## SSH agent config
#
zstyle :omz:plugins:ssh-agent agent-forwarding on
zstyle :omz:plugins:ssh-agent identities id_ed25519 id_rsa seanb4t_ed25519
zstyle :omz:plugins:ssh-agent ssh-add-args -K -k -q --apple-use-keychain --apple-load-keychain


[[ -d ~/go/bin ]] && export PATH="${HOME}/go/bin:${PATH}"
