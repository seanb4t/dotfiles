function kgdw --wraps=\'watch\ kubectl\ get\ deployments\' --wraps='watch kubectl get deployments' --description 'alias kgdw=watch kubectl get deployments'
  watch kubectl get deployments $argv; 
end
