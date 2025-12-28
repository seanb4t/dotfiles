# for github cli

if type -q gh
  gh completion -s fish | source
  # export GH_TOKEN if authenticated
  if gh auth status > /dev/null 2>&1
    set -gx GH_TOKEN (gh auth token)
  end
end
