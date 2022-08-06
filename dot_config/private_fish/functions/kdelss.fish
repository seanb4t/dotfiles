function kdelss --wraps=\'kubectl\ delete\ statefulset\' --wraps='kubectl delete statefulset' --description 'alias kdelss=kubectl delete statefulset'
  kubectl delete statefulset $argv; 
end
