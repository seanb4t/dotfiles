function kgjy --wraps=\'kubectl\ get\ jobs\ -o\ yaml\' --wraps='kubectl get jobs -o yaml' --description 'alias kgjy=kubectl get jobs -o yaml'
  kubectl get jobs -o yaml $argv; 
end
