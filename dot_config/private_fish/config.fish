if status is-interactive
  # Commands to run in interactive sessions can go here

  kubectl completion fish | source
end

set -Ux EDITOR nvim
set -Ux VISUAL nvim
set -Ux PAGER less
set -Ux LESS "-R -M -X"

