function kdcm --wraps=\'kubectl\ delete\ configmaps\' --wraps='kubectl delete configmaps' --description 'alias kdcm=kubectl delete configmaps'
  kubectl delete configmaps $argv; 
end
