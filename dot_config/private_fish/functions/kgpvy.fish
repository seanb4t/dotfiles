function kgpvy --wraps=\'kubectl\ get\ persistentvolumes\ -o\ yaml\' --wraps='kubectl get persistentvolumes -o yaml' --description 'alias kgpvy=kubectl get persistentvolumes -o yaml'
  kubectl get persistentvolumes -o yaml $argv; 
end
