function kg --wraps=\'kubectl\ get\' --wraps='kubectl get' --description 'alias kg=kubectl get'
  kubectl get $argv; 
end
