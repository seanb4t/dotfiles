function ken --wraps=\'kubectl\ edit\ nodes\' --wraps='kubectl edit nodes' --description 'alias ken=kubectl edit nodes'
  kubectl edit nodes $argv; 
end
