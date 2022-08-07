if status is-interactive
  # Commands to run in interactive sessions can go here

  # Third party completions
  ## kubectl / kubernetes
  command -v kubectl > /dev/null && kubectl completion fish | source

  ## helm completion
  command -v helm > /dev/null && helm completion fish | source

  if command -v op > /dev/null
    ## 1password cli completion, unset connect related vars
    set -u OP_CONNECT_HOST
    set -u OP_CONNECT_TOKEN
    op completion fish | source
  end

  # flux
  command -v flux > /dev/null && flux completion fish | source

end

set -gx EDITOR nvim
set -gx VISUAL nvim
set -gx PAGER less
set -gx LESS "-R -M -X"

# configure brew vars
set -gx HOMEBREW_NO_ENV_HINTS 1

# do not wrap ls with grc
set -gx -a grc_plugin_ignore_execs ls exa

# set gpg tty
set -gx GPG_TTY (tty)
