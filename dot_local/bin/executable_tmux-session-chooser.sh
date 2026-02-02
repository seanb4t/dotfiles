#!/bin/bash
# Tmux session chooser for Ghostty startup

# Add homebrew to PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# If already inside tmux, just start shell
if [ -n "$TMUX" ]; then
    exec $SHELL
fi

# List existing sessions
SESSIONS=$(/opt/homebrew/bin/tmux list-sessions -F "#{session_name}" 2>/dev/null | sort)

if [ -z "$SESSIONS" ]; then
    # No sessions exist - create default one
    exec /opt/homebrew/bin/tmux new-session
fi

# Requires fzf (brew install fzf)
if ! command -v fzf &> /dev/null; then
    echo "fzf not installed. Installing via homebrew..."
    brew install fzf
fi

# Use fzf to choose
CHOICE=$(echo -e "$SESSIONS\n+ Create new session" | fzf \
    --height=40% \
    --reverse \
    --border \
    --prompt="Select tmux session: " \
    --header="Press ESC to start without tmux")

if [ "$CHOICE" = "+ Create new session" ]; then
    read -r -p "Session name: " SESSION_NAME
    if [ -n "$SESSION_NAME" ]; then
        exec /opt/homebrew/bin/tmux new-session -s "$SESSION_NAME"
    else
        exec /opt/homebrew/bin/tmux new-session
    fi
elif [ -n "$CHOICE" ]; then
    exec /opt/homebrew/bin/tmux attach-session -t "$CHOICE"
else
    # User cancelled - start shell without tmux
    exec $SHELL
fi
