#!/usr/bin/env fish

if test -f ~/.cargo/env.fish
    source ~/.cargo/env.fish
else
    if not test -d ~/.rustup
        echo "rustup-init has not been run. Running rustup-init..."
        rustup-init --profile complete --no-modify-path -y
        source ~/.cargo/env.fish
    end
end