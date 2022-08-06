function kgs --wraps=\'kubectl\ get\ services\' --wraps='kubectl get services' --description 'alias kgs=kubectl get services'
  kubectl get services $argv; 
end
