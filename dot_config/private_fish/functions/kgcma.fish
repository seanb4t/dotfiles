function kgcma --wraps=\'kubectl\ get\ configmaps\ --all-namespaces\' --wraps='kubectl get configmaps --all-namespaces' --description 'alias kgcma=kubectl get configmaps --all-namespaces'
  kubectl get configmaps --all-namespaces $argv; 
end
