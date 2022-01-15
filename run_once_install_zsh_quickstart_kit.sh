#!/usr/bin/env zsh

set -e

git clone git@github.com:unixorn/zsh-quickstart-kit.git "${HOME}/.zsh_quickstart_kit"
[[ -d ~/.fzf ]] || git clone --depth 1 https://github.com/junegunn/fzf.git "${HOME}/.fzf"

( cd  "${HOME}/.zsh_quickstart_kit" && stow --target="${HOME}" zsh )

