# direnv integration (per-directory environment variables)
if type -q direnv; and status is-interactive
    direnv hook fish | source
end
