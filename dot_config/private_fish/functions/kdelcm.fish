function kdelcm --wraps=\'kubectl\ delete\ configmap\' --wraps='kubectl delete configmap' --description 'alias kdelcm=kubectl delete configmap'
  kubectl delete configmap $argv; 
end
