function ke --wraps=\'kubectl\ edit\' --wraps='kubectl edit' --description 'alias ke=kubectl edit'
  kubectl edit $argv; 
end
