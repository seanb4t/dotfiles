# Source native grc (colorized command output)
if type -q grc; and test -f /opt/homebrew/etc/grc.fish
    source /opt/homebrew/etc/grc.fish
    # Remove ls wrapper — eza handles it via fish-eza plugin
    functions -e ls
end
