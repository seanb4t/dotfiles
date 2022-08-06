function kgdsy --wraps=\'kubectl\ get\ daemonsets\ -o\ yaml\' --wraps='kubectl get daemonsets -o yaml' --description 'alias kgdsy=kubectl get daemonsets -o yaml'
  kubectl get daemonsets -o yaml $argv; 
end
