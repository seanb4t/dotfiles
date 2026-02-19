
set -U fisher_path $__fish_config_dir/fisher

if not test -d $fisher_path
    mkdir -p $fisher_path
end

set fish_complete_path $fish_complete_path[1] $fisher_path/completions $fish_complete_path[2..]
set fish_function_path $fish_function_path[1] $fisher_path/functions $fish_function_path[2..]

# sdkman-for-fish warns when SDKMAN_DIR is exported but SDKMAN! is not installed.
if set -q SDKMAN_DIR; and not test -f "$SDKMAN_DIR/bin/sdkman-init.sh"
    set -e SDKMAN_DIR
end

for file in $fisher_path/conf.d/*.fish
    source $file
end
