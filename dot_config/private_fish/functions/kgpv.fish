function kgpv --wraps=\'kubectl\ get\ persistentvolumes\' --wraps='kubectl get persistentvolumes' --description 'alias kgpv=kubectl get persistentvolumes'
  kubectl get persistentvolumes $argv; 
end
