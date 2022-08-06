function kdpv --wraps=\'kubectl\ delete\ persistentvolumes\' --wraps='kubectl delete persistentvolumes' --description 'alias kdpv=kubectl delete persistentvolumes'
  kubectl delete persistentvolumes $argv; 
end
