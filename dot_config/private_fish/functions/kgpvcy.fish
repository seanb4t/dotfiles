function kgpvcy --wraps=\'kubectl\ get\ persistentvolumeclaims\ -o\ yaml\' --wraps='kubectl get persistentvolumeclaims -o yaml' --description 'alias kgpvcy=kubectl get persistentvolumeclaims -o yaml'
  kubectl get persistentvolumeclaims -o yaml $argv; 
end
