function kepv --wraps=\'kubectl\ edit\ persistentvolumes\' --wraps='kubectl edit persistentvolumes' --description 'alias kepv=kubectl edit persistentvolumes'
  kubectl edit persistentvolumes $argv; 
end
