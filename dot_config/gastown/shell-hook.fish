# Gas Town Shell Integration (Fish)
# Installed by: gt install --shell
# Location: ~/.config/gastown/shell-hook.fish

function _gastown_enabled
    test -n "$GASTOWN_DISABLED"; and return 1
    test -n "$GASTOWN_ENABLED"; and return 0
    set -l state_file "$HOME/.local/state/gastown/state.json"
    test -f "$state_file"; and grep -q '"enabled":\s*true' "$state_file" 2>/dev/null
end

function _gastown_ignored
    set -l dir "$PWD"
    while test "$dir" != /
        test -f "$dir/.gastown-ignore"; and return 0
        set dir (dirname "$dir")
    end
    return 1
end

function _gastown_already_asked
    set -l repo_root $argv[1]
    set -l asked_file "$HOME/.cache/gastown/asked-repos"
    test -f "$asked_file"; and grep -qF "$repo_root" "$asked_file" 2>/dev/null
end

function _gastown_mark_asked
    set -l repo_root $argv[1]
    set -l asked_file "$HOME/.cache/gastown/asked-repos"
    mkdir -p (dirname "$asked_file")
    echo "$repo_root" >> "$asked_file"
end

function _gastown_bash_to_fish
    # Convert bash export/unset syntax to fish equivalents
    # export VAR="value" → set -gx VAR "value"
    # unset VAR → set -e VAR
    string replace -r -a 'export (\w+)="([^"]*)"' 'set -gx $1 "$2"' $argv | \
        string replace -r -a 'export (\w+)=(\S+)' 'set -gx $1 $2' | \
        string replace -r -a 'unset (\w+)' 'set -e $1'
end

function _gastown_offer_add
    set -l repo_root $argv[1]

    _gastown_already_asked "$repo_root"; and return 0

    test -t 0; or return 0

    set -l repo_name (basename "$repo_root")

    echo ""
    read -P "Add '$repo_name' to Gas Town? [y/N/never] " response

    _gastown_mark_asked "$repo_root"

    switch "$response"
        case y Y yes
            echo "Adding to Gas Town..."
            set -l output (gt rig quick-add "$repo_root" --yes 2>&1)
            set -l exit_code $status
            echo "$output"

            if test $exit_code -eq 0
                set -l crew_path (echo "$output" | grep "^GT_CREW_PATH=" | cut -d= -f2)
                if test -n "$crew_path" -a -d "$crew_path"
                    echo ""
                    echo "Switching to crew workspace..."
                    cd "$crew_path"
                    _gastown_hook
                end
            end
        case never
            touch "$repo_root/.gastown-ignore"
            echo "Created .gastown-ignore - won't ask again for this repo."
        case '*'
            echo "Skipped. Run 'gt rig quick-add' later to add manually."
    end
end

function _gastown_hook --on-variable PWD
    set -l previous_exit_status $status

    _gastown_enabled; or begin
        set -e GT_TOWN_ROOT
        set -e GT_RIG
        return $previous_exit_status
    end

    _gastown_ignored; and begin
        set -e GT_TOWN_ROOT
        set -e GT_RIG
        return $previous_exit_status
    end

    if not git rev-parse --git-dir &>/dev/null
        set -e GT_TOWN_ROOT
        set -e GT_RIG
        return $previous_exit_status
    end

    set -l repo_root (git rev-parse --show-toplevel 2>/dev/null); or begin
        set -e GT_TOWN_ROOT
        set -e GT_RIG
        return $previous_exit_status
    end

    set -l cache_file "$HOME/.cache/gastown/rigs.cache"
    if test -f "$cache_file"
        set -l cached (grep "^$repo_root:" "$cache_file" 2>/dev/null)
        if test -n "$cached"
            # cached line format: /path/to/repo:GT_TOWN_ROOT=x GT_RIG=y
            set -l assignments (string replace "$repo_root:" "" "$cached")
            eval (_gastown_bash_to_fish "$assignments")
            return $previous_exit_status
        end
    end

    if type -q gt
        set -l detect_output (gt rig detect "$repo_root" 2>/dev/null)
        eval (_gastown_bash_to_fish "$detect_output")

        if test -n "$GT_TOWN_ROOT"
            gt rig detect --cache "$repo_root" &>/dev/null &
        else if set -q _GASTOWN_OFFER_ADD
            _gastown_offer_add "$repo_root"
            set -e _GASTOWN_OFFER_ADD
        end
    end

    return $previous_exit_status
end

# Also run on each prompt to catch cases where PWD didn't change
# but we still need to detect (e.g., initial shell, after gt commands)
function _gastown_prompt_hook --on-event fish_prompt
    _gastown_enabled; or return
    _gastown_ignored; and return

    # Only run full detection if GT vars aren't set and we're in a git repo
    if not set -q GT_TOWN_ROOT
        if git rev-parse --git-dir &>/dev/null
            set -l repo_root (git rev-parse --show-toplevel 2>/dev/null)
            if test -n "$repo_root"
                set -l cache_file "$HOME/.cache/gastown/rigs.cache"
                if test -f "$cache_file"
                    set -l cached (grep "^$repo_root:" "$cache_file" 2>/dev/null)
                    if test -n "$cached"
                        set -l assignments (string replace "$repo_root:" "" "$cached")
                        eval (_gastown_bash_to_fish "$assignments")
                    end
                end
            end
        end
    end
end

# Run once on shell startup
_gastown_hook
