function kepvc --wraps=\'kubectl\ edit\ persistentvolumeclaims\' --wraps='kubectl edit persistentvolumeclaims' --description 'alias kepvc=kubectl edit persistentvolumeclaims'
  kubectl edit persistentvolumeclaims $argv; 
end
