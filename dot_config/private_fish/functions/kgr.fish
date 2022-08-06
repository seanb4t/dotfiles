function kgr --wraps=\'kubectl\ get\ roles\' --wraps='kubectl get roles' --description 'alias kgr=kubectl get roles'
  kubectl get roles $argv; 
end
