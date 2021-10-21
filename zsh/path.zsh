# -*- mode: sh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# code: language=shell insertSpaces=true tabSize=2

# Set the list of directories that Zsh searches for programs.
path=(
  ~/.{local,cargo}/bin
  /usr/local/{bin,sbin}
  $path
)

[[ -d /home/linuxbrew/.linuxbrew/bin ]] && path=(
  /home/linuxbrew/.linuxbrew/{bin,sbin}
  $path
)
