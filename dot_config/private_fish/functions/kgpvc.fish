function kgpvc --wraps=\'kubectl\ get\ persistentvolumeclaims\' --wraps='kubectl get persistentvolumeclaims' --description 'alias kgpvc=kubectl get persistentvolumeclaims'
  kubectl get persistentvolumeclaims $argv; 
end
