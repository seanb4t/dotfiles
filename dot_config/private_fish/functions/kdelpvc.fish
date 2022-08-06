function kdelpvc --wraps=\'kubectl\ delete\ pvc\' --wraps='kubectl delete pvc' --description 'alias kdelpvc=kubectl delete pvc'
  kubectl delete pvc $argv; 
end
