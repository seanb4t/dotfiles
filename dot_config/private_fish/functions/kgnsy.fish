function kgnsy --wraps=\'kubectl\ get\ namespaces\ -o\ yaml\' --wraps='kubectl get namespaces -o yaml' --description 'alias kgnsy=kubectl get namespaces -o yaml'
  kubectl get namespaces -o yaml $argv; 
end
