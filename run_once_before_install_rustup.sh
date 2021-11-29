#!/usr/bin/env zsh

curl --proto '=https' --tlsv1.2 -sSf -o /tmp/rustup-init.zsh  https://sh.rustup.rs
zsh /tmp/rustup-init.zsh -q -y
rm /tmp/rustup-init.zsh
