function kdelsec --wraps=\'kubectl\ delete\ secret\' --wraps='kubectl delete secret' --description 'alias kdelsec=kubectl delete secret'
  kubectl delete secret $argv; 
end
