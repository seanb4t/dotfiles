function kgcr --wraps=\'kubectl\ get\ clusterroles\' --wraps='kubectl get clusterroles' --description 'alias kgcr=kubectl get clusterroles'
  kubectl get clusterroles $argv; 
end
