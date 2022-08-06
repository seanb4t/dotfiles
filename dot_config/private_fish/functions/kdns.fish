function kdns --wraps=\'kubectl\ delete\ namespaces\' --wraps='kubectl delete namespaces' --description 'alias kdns=kubectl delete namespaces'
  kubectl delete namespaces $argv; 
end
