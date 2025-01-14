
if type -q talosctl
    talosctl completion fish | source
end

if test -f (dirname (realpath (status --current-filename)))/kubectl_aliases
    source (dirname (realpath (status --current-filename)))/kubectl_aliases
end

# build KUBECONFIG from ~/.kube/configs/*.yml and ~/.kube/config, using ; as separator
set -x KUBECONFIG (ls ~/.kube/configs/*.yml ~/.kube/config | string join ":")

