function kej --wraps=\'kubectl\ edit\ jobs\' --wraps='kubectl edit jobs' --description 'alias kej=kubectl edit jobs'
  kubectl edit jobs $argv; 
end
