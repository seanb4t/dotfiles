function kdspv --wraps=\'kubectl\ describe\ persistentvolumes\' --wraps='kubectl describe persistentvolumes' --description 'alias kdspv=kubectl describe persistentvolumes'
  kubectl describe persistentvolumes $argv; 
end
