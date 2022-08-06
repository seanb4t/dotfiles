function kds --wraps=\'kubectl\ delete\ services\' --wraps='kubectl delete services' --description 'alias kds=kubectl delete services'
  kubectl delete services $argv; 
end
