function kdp --wraps=\'kubectl\ delete\ pod\' --wraps='kubectl delete pod' --description 'alias kdp=kubectl delete pod'
  kubectl delete pod $argv; 
end
