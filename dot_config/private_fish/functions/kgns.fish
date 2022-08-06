function kgns --wraps=\'kubectl\ get\ namespaces\' --wraps='kubectl get namespaces' --description 'alias kgns=kubectl get namespaces'
  kubectl get namespaces $argv; 
end
