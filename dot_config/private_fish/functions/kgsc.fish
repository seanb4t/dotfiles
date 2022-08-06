function kgsc --wraps=\'kubectl\ get\ secrets\' --wraps='kubectl get secrets' --description 'alias kgsc=kubectl get secrets'
  kubectl get secrets $argv; 
end
