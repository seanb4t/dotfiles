function kgcrv --wraps=\'kubectl\ get\ controllerrevisions\' --wraps='kubectl get controllerrevisions' --description 'alias kgcrv=kubectl get controllerrevisions'
  kubectl get controllerrevisions $argv; 
end
