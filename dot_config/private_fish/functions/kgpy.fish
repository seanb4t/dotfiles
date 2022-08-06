function kgpy --wraps=\'kubectl\ get\ pods\ -o\ yaml\' --wraps='kubectl get pods -o yaml' --description 'alias kgpy=kubectl get pods -o yaml'
  kubectl get pods -o yaml $argv; 
end
