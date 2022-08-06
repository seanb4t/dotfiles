function kgn --wraps=\'kubectl\ get\ nodes\' --wraps='kubectl get nodes' --description 'alias kgn=kubectl get nodes'
  kubectl get nodes $argv; 
end
