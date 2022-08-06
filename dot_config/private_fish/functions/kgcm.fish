function kgcm --wraps=\'kubectl\ get\ configmaps\' --wraps='kubectl get configmaps' --description 'alias kgcm=kubectl get configmaps'
  kubectl get configmaps $argv; 
end
