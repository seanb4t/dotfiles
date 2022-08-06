function kgrs --wraps=\'kubectl\ get\ replicaset\' --wraps='kubectl get replicaset' --description 'alias kgrs=kubectl get replicaset'
  kubectl get replicaset $argv; 
end
