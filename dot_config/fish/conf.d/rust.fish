#!/usr/bin/env fish

# ~/.config/fish/conf.d/rust.fish
fish_add_path -g $HOMEBREW_PREFIX/opt/rustup/bin
fish_add_path -g $HOME/.cargo/bin

if test -f ~/.cargo/env.fish
    source ~/.cargo/env.fish
else
    if not test -d ~/.rustup
        echo "rustup-init has not been run. Running rustup-init..."
        rustup-init --profile complete --no-modify-path -y
        source ~/.cargo/env.fish
    end
end
