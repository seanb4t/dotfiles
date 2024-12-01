#!/usr/bin/env bash

# if ~/.rustup does not exist, then rustup-init has not been run
if [ ! -d "$HOME/.rustup" ]; then
    echo "rustup-init has not been run. Running rustup-init..."
    rustup-init --profile complete --no-modify-path -y
fi