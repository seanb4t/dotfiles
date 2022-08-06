function kdsn --wraps=\'kubectl\ describe\ nodes\' --wraps='kubectl describe nodes' --description 'alias kdsn=kubectl describe nodes'
  kubectl describe nodes $argv; 
end
