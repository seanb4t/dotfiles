function kgaa --wraps='kga -A' --wraps=\'kubectl\ get\ all\ --all-namespaces\' --wraps='kubectl get all --all-namespaces' --description 'alias kgaa=kubectl get all --all-namespaces'
  kubectl get all --all-namespaces $argv; 
end
