function kcn --wraps=\'kubectl\ config\ set-context\ --current\ --namespace\' --wraps='kubectl config set-context --current --namespace' --description 'alias kcn=kubectl config set-context --current --namespace'
  kubectl config set-context --current --namespace $argv; 
end
