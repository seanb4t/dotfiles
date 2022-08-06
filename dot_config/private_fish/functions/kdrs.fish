function kdrs --wraps=\'kubectl\ describe\ replicaset\' --wraps='kubectl describe replicaset' --description 'alias kdrs=kubectl describe replicaset'
  kubectl describe replicaset $argv; 
end
