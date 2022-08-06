function kgpvca --wraps=\'kubectl\ get\ pvc\ --all-namespaces\' --wraps='kubectl get pvc --all-namespaces' --description 'alias kgpvca=kubectl get pvc --all-namespaces'
  kubectl get pvc --all-namespaces $argv; 
end
