function kgsec --wraps=\'kubectl\ get\ secret\' --wraps='kubectl get secret' --description 'alias kgsec=kubectl get secret'
  kubectl get secret $argv; 
end
