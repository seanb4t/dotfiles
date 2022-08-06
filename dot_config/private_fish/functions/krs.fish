function krs --wraps=\'kubectl\ get\ replicasets\' --wraps='kubectl get replicasets' --description 'alias krs=kubectl get replicasets'
  kubectl get replicasets $argv; 
end
