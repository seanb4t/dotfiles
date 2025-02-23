
if type -q talosctl
    talosctl completion fish | source
end

if test -f (dirname (realpath (status --current-filename)))/kubectl_aliases
    source (dirname (realpath (status --current-filename)))/kubectl_aliases
end

# If ~/.kube/config exists, set KUBECONFIG
if test -f ~/.kube/config
  set -x KUBECONFIG ~/.kube/config
else
  set -x KUBECONFIG ""
end

# If there are any *.yml files in ~/.kube/configs, add them to KUBECONFIG
if test -d ~/.kube/configs
  for file in ~/.kube/configs/*.yml
      # Only proceed if the file actually exists (pattern may not expand)
      if test -f $file
          if test -z $KUBECONFIG
              # If KUBECONFIG is empty, set it directly
              set -x KUBECONFIG $file
          else
              # Otherwise, append with a colon
              set -x KUBECONFIG $KUBECONFIG:$file
          end
      end
  end
end
