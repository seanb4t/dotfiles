function kdpvc --wraps=\'kubectl\ delete\ persistentvolumeclaims\' --wraps='kubectl delete persistentvolumeclaims' --description 'alias kdpvc=kubectl delete persistentvolumeclaims'
  kubectl delete persistentvolumeclaims $argv; 
end
