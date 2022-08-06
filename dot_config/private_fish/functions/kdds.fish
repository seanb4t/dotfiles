function kdds --wraps=\'kubectl\ delete\ daemonsets\' --wraps='kubectl delete daemonsets' --description 'alias kdds=kubectl delete daemonsets'
  kubectl delete daemonsets $argv; 
end
