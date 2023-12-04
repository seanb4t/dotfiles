
if test -f (dirname (realpath (status --current-filename)))/kubectl_aliases
  source (dirname (realpath (status --current-filename)))/kubectl_aliases
end

