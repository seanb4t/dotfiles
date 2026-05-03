
# if GHOSTTY_RESOURCES_DIR os set load the resources
if test -n "$GHOSTTY_RESOURCES_DIR"
    set -l _gsi "$GHOSTTY_RESOURCES_DIR"/shell-integration/fish/vendor_conf.d/ghostty-shell-integration.fish
    test -f "$_gsi"; and source "$_gsi"
end