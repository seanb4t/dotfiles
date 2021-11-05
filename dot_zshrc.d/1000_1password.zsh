#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

if (( ${+commands[op]} )); then
  eval "$(op completion zsh)"
  compdef _op op
fi

# This function will run `op signin` with any supplied arguments and eval the
# command into the current shell.
function 1ps() {
    eval $(command op signin "$@")
    return $?
}

# opswd puts the password of the named service into the clipboard. If there's a
# one time password, it will be copied into the clipboard after 5 seconds. The
# clipboard is cleared after another 10 seconds.
function opswd() {
  if [[ $# -lt 1 ]]; then
    echo "Usage: opswd <service>"
    return 1
  fi

  local service=$1

  # If not logged in, print error and return
  op list users > /dev/null || return

  op get item "$service" \
  | jq -r '.details.fields[] | select(.designation=="password").value' \
  | clipcopy

  (
    sleep 5 && op get totp "$service" 2>/dev/null | clipcopy 2>/dev/null
    sleep 10 && clipcopy < /dev/null 2>/dev/null &
  ) &!
}

function _opswd() {
  local -a services
  services=("${(@f)$(op list items --categories Login 2>/dev/null | jq -r '.[].overview.title')}")
  [[ -z "$services" ]] || compadd -a -- services
}

compdef _opswd opswd