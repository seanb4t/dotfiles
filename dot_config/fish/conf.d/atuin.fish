if type -q atuin; and status is-interactive
  atuin init fish | source

  # Disable fzf.fish history search (Ctrl+R) — atuin owns it
  fzf_configure_bindings --history=
end
