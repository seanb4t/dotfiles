function kdelds --wraps=\'kubectl\ delete\ daemonset\' --wraps='kubectl delete daemonset' --description 'alias kdelds=kubectl delete daemonset'
  kubectl delete daemonset $argv; 
end
