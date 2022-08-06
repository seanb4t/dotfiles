function kdss --wraps=\'kubectl\ describe\ services\' --wraps='kubectl describe services' --description 'alias kdss=kubectl describe services'
  kubectl describe services $argv; 
end
