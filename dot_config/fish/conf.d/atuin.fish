if type -q atuin and is-interactive
  #TODO: bug, review later
  set -gx ATUIN_TMUX_POPUP false
  atuin init fish | source
end
