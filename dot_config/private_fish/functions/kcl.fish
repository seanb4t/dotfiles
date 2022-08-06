function kcl --wraps=\'kubectl\ logs\' --wraps='kubectl logs' --description 'alias kcl=kubectl logs'
  kubectl logs $argv; 
end
