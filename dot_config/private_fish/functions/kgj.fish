function kgj --wraps=\'kubectl\ get\ jobs\' --wraps='kubectl get jobs' --description 'alias kgj=kubectl get jobs'
  kubectl get jobs $argv; 
end
