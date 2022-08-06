function kgcmy --wraps=\'kubectl\ get\ configmaps\ -o\ wide\' --wraps='kubectl get configmaps -o wide' --description 'alias kgcmy=kubectl get configmaps -o wide'
  kubectl get configmaps -o wide $argv; 
end
