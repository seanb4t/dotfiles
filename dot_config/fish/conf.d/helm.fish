if type -q helm
  helm completion fish | source
  if not helm plugin list | grep -q "diff"
    helm plugin install https://github.com/databus23/helm-diff
  end
end
