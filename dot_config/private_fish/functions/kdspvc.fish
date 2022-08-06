function kdspvc --wraps=\'kubectl\ describe\ persistentvolumeclaims\' --wraps='kubectl describe persistentvolumeclaims' --description 'alias kdspvc=kubectl describe persistentvolumeclaims'
  kubectl describe persistentvolumeclaims $argv; 
end
