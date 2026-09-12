if type -q atuin; and status is-interactive
  # Disable fzf history first: its cleanup erases the current Ctrl+R binding.
  fzf_configure_bindings --history=

  atuin init fish | source
end
