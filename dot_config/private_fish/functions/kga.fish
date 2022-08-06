function kga --wraps='k get all' --wraps=\'kubectl\ get\ --all-namespaces\' --wraps='kubectl get --all-namespaces' --description 'alias kga=kubectl get --all-namespaces'
  kubectl get --all-namespaces $argv; 
end
