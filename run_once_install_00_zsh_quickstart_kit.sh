#!/usr/bin/env zsh

set -e

[[ -d /home/linuxbrew ]] && export PATH=/home/linuxbrew/.linuxbrew/bin:$PATH
[[ -d /opt/homebrew ]] && export PATH=/opt/homebrew/bin:$PATH

if [[ -d "${HOME}/.zsh_quickstart_kit" ]]; then
  cd "${HOME}/.zsh_quickstart_kit"
  git pull
else
  git clone git@github.com:seanb4t/zsh-quickstart-kit.git "${HOME}/.zsh_quickstart_kit"
fi

[[ -d ~/.fzf ]] || git clone --depth 1 https://github.com/junegunn/fzf.git "${HOME}/.fzf"

rm -rf ~/.zshrc ~/.zshrc.local ~/.zshrc.pre-oh-my-zsh ~/.zshenv ~/.zshrc.d

( cd  "${HOME}/.zsh_quickstart_kit" && stow --target="${HOME}" zsh )

