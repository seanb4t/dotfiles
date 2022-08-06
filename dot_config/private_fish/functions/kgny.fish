function kgny --wraps=\'kubectl\ get\ nodes\ -o\ yaml\' --wraps='kubectl get nodes -o yaml' --description 'alias kgny=kubectl get nodes -o yaml'
  kubectl get nodes -o yaml $argv; 
end
