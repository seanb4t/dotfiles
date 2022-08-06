function kgscy --wraps=\'kubectl\ get\ secrets\ -o\ yaml\' --wraps='kubectl get secrets -o yaml' --description 'alias kgscy=kubectl get secrets -o yaml'
  kubectl get secrets -o yaml $argv; 
end
