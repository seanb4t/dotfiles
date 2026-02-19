if type -q helm
  helm completion fish | source
  if status is-interactive; and not helm plugin list | grep -q "diff"
    helm plugin install --verify=false https://github.com/databus23/helm-diff
  end
end
