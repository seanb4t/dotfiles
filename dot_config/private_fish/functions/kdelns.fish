function kdelns --wraps=\'kubectl\ delete\ namespace\' --wraps='kubectl delete namespace' --description 'alias kdelns=kubectl delete namespace'
  kubectl delete namespace $argv; 
end
