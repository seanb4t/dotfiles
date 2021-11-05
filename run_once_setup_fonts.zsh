#!/usr/bin/env zsh
# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
install() {
        curl -L -s -o "$1/SourceCodePro-Light.ttf" \
                https://github.com/adobe-fonts/source-code-pro/raw/release/TTF/SourceCodePro-Light.ttf
}

if [ "$(uname -s)" = "Darwin" ]; then
        if command -v brew >/dev/null 2>&1; then
                brew tap | grep -q homebrew/cask-fonts || brew tap homebrew/cask-fonts
                brew install font-jetbrains-mono \
                        font-jetbrains-mono-nerd-font \
                        font-fira-code-nerd-font \
                        font-meslo-for-powerline \
                        font-meslo-lg \
                        font-meslo-lg-dz \
                        font-meslo-lg-nerd-font
        else
                install ~/Library/Fonts
        fi
else
        mkdir -p ~/.fonts
        install ~/.fonts
fi
