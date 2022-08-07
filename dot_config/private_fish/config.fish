if status is-interactive
  # Commands to run in interactive sessions can go here

  # Third party completions
  ## kubectl / kubernetes
  kubectl completion fish | source

  ## helm completion
  helm completion fish | source

  ## 1password cli completion, unset connect related vars
  set -u OP_CONNECT_HOST
  set -u OP_CONNECT_TOKEN
  op completion fish | source
  # flux
  flux completion fish | source

end

set -gx EDITOR nvim
set -gx VISUAL nvim
set -gx PAGER less
set -gx LESS "-R -M -X"

