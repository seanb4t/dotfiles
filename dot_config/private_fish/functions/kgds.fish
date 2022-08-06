function kgds --wraps=\'kubectl\ get\ daemonsets\' --wraps='kubectl get daemonsets' --description 'alias kgds=kubectl get daemonsets'
  kubectl get daemonsets $argv; 
end
