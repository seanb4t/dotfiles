function kgda --wraps=\'kubectl\ get\ deployment\ --all-namespaces\' --wraps='kubectl get deployment --all-namespaces' --description 'alias kgda=kubectl get deployment --all-namespaces'
  kubectl get deployment --all-namespaces $argv; 
end
