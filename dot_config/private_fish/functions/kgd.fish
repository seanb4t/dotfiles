function kgd --wraps=\'kubectl\ get\ deployments\' --wraps='kubectl get deployments' --description 'alias kgd=kubectl get deployments'
  kubectl get deployments $argv; 
end
