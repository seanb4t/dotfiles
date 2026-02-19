function chezmoi --wraps chezmoi
    # Check for existing 1Password session via env vars first (cheap),
    # then fall back to op whoami (works with app integration)
    set -l has_session false
    for var in (set -n)
        if string match -q 'OP_SESSION_*' $var; or test "$var" = OP_SERVICE_ACCOUNT_TOKEN
            set has_session true
            break
        end
    end

    if not $has_session; and not op whoami &>/dev/null
        echo "Not signed in to 1Password. Please run:"
        echo "  eval (op signin --account fzymgc.1password.com)"
        return 1
    end
    command chezmoi $argv
end
