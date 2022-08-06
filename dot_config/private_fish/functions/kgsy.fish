function kgsy --wraps=\'kubectl\ get\ services\ -o\ yaml\' --wraps='kubectl get services -o yaml' --description 'alias kgsy=kubectl get services -o yaml'
  kubectl get services -o yaml $argv; 
end
