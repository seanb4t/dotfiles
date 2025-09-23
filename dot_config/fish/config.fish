if status is-interactive
  # Interactive config here

  set -gx ZELLIJ_CONFIG_DIR ~/.config/zellij

  #if [ "$TERM" = "xterm-ghostty" ]
  #  # launch zellij
  #  eval (zellij setup --generate-auto-start fish | string collect )
  #end

  # Configure kubernetes completions
  kubectl completion fish | source

  # Configure Orb
  if type -q orbctl
    orbctl completion fish | source
  end

  # Configure Starship Prompt, do not run if cursor agent is active or unset or TERM_PROGRAM is either cursor or vscode
  if [ "$CURSOR_AGENT" = 0 -o -z "$CURSOR_AGENT" -o "$TERM_PROGRAM" = "cursor" -o "$TERM_PROGRAM" = "vscode" ]
    starship init fish | source
  end

  # Aliases

end

# Set fish greeting
set --global fish_greeting ""

# Set sane TERM value
set -gx TERM xterm-256color

# Set paths
fish_add_path -p -m $HOME/.local/bin


# Set up editor and related vars
set -gx EDITOR nvim
set -gx VISUAL nvim
set -gx GIT_EDITOR nvim

# Setup pager
set -gx PAGER bat

# Setup go
set -g GOPATH $HOME/go
fish_add_path $GOPATH/bin

# Setup rust/cargo
fish_add_path $HOME/.cargo/bin


# Configure krew
set -q KREW_ROOT; and fish_add_path $KREW_ROOT/.krew/bin; or fish_add_path $HOME/.krew/bin


switch (uname)
  case Darwin
    source (dirname (status --current-filename))/config-osx.fish
  case Linux
    source (dirname (status --current-filename))/config-linux.fish
  case '*'
    source (dirname (status --current-filename))/config-windows.fish
end

set LOCAL_CONFIG (dirname (status --current-filename))/config-local.fish
if test -f $LOCAL_CONFIG
  source $LOCAL_CONFIG
end

set -gx WEZTERM_THEME tokyonightstorm

# bun
set --export BUN_INSTALL "$HOME/.bun"
set --export PATH $BUN_INSTALL/bin $PATH
