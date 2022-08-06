function ktn --wraps=\'kubectl\ top\ nodes\' --wraps='kubectl top nodes' --description 'alias ktn=kubectl top nodes'
  kubectl top nodes $argv; 
end
