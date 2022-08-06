function kgep --wraps=\'kubectl\ get\ endpoints\' --wraps='kubectl get endpoints' --description 'alias kgep=kubectl get endpoints'
  kubectl get endpoints $argv; 
end
