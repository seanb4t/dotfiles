function kcsc --wraps=\'kubectl\ config\ set-context\' --wraps='kubectl config set-context' --description 'alias kcsc=kubectl config set-context'
  kubectl config set-context $argv; 
end
