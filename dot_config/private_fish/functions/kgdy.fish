function kgdy --wraps=\'kubectl\ get\ deployments\ -o\ yaml\' --wraps='kubectl get deployments -o yaml' --description 'alias kgdy=kubectl get deployments -o yaml'
  kubectl get deployments -o yaml $argv; 
end
