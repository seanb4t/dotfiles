#!/usr/bin/env bash

# Ensure fish is in /etc/shells
if ! grep -q "/opt/homebrew/bin/fish" /etc/shells; then
    echo "Adding fish to /etc/shells, you may be prompted for your password"
    echo "/opt/homebrew/bin/fish" | sudo tee -a /etc/shells
fi

# Set shell to homebrew's fish
# if dscl user shell does not match /opt/homebrew/bin/fish set it correctly with chsh
if [ "$(dscl . -read /Users/$USER UserShell | awk '{print $2}')" != "/opt/homebrew/bin/fish" ]; then
    echo "Changing shell to fish, you may be prompted for your password"
    user="$(id -nu)"
    sudo chsh -s /opt/homebrew/bin/fish "$user"
fi