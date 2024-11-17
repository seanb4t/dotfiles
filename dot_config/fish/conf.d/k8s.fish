
if type -q switcher
    switcher init fish | source
    alias kctx=kubeswitch
    alias kubectx=kubeswitch
end

if type -q talosctl
    talosctl completion fish | source
end

if test -f (dirname (realpath (status --current-filename)))/kubectl_aliases
    source (dirname (realpath (status --current-filename)))/kubectl_aliases
end
