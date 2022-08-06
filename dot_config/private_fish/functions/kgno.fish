function kgno --wraps=\'kubectl\ get\ nodes\' --wraps='kubectl get nodes' --description 'alias kgno=kubectl get nodes'
  kubectl get nodes $argv; 
end
