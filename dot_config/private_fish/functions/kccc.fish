function kccc --wraps=\'kubectl\ config\ current-context\' --wraps='kubectl config current-context' --description 'alias kccc=kubectl config current-context'
  kubectl config current-context $argv; 
end
