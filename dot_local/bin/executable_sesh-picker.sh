#!/bin/bash
# sesh session picker for tmux popup
target=$(sesh list --icons | fzf-tmux -p 85%,75% \
  --no-sort --ansi --border-label ' sesh ' --prompt '⚡  ' \
  --header-first \
  --header '  ^a all ^t tmux ^g config ^x zoxide
  ^f find ^d kill | type + enter to create' \
  --bind 'tab:down,btab:up' \
  --bind 'ctrl-a:change-prompt(⚡  )+reload(sesh list --icons)' \
  --bind 'ctrl-t:change-prompt(🪟  )+reload(sesh list -t --icons)' \
  --bind "ctrl-g:change-prompt(⚙️  )+reload(sesh list -c --icons)" \
  --bind 'ctrl-x:change-prompt(📁  )+reload(sesh list -z --icons)' \
  --bind "ctrl-f:change-prompt(🔎  )+reload(fd -H -d 2 -t d -E .Trash . ~)" \
  --bind 'ctrl-d:execute(tmux kill-session -t {2..})+change-prompt(⚡  )+reload(sesh list --icons)' \
  --preview-window 'right:55%' \
  --preview 'sesh preview {}' \
  --print-query \
  | tail -n 1)

[ -z "$target" ] && exit 0

# Try sesh first (existing sessions, dirs, zoxide); fall back to creating new tmux session
sesh connect "$target" 2>/dev/null \
  || (tmux new-session -d -s "$target" 2>/dev/null && tmux switch-client -t "$target")

exit 0
