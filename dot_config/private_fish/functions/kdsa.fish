function kdsa --wraps=\'kubectl\ describe\ sa\' --wraps='kubectl describe sa' --description 'alias kdsa=kubectl describe sa'
  kubectl describe sa $argv; 
end
