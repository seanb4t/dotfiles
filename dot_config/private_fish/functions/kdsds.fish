function kdsds --wraps=\'kubectl\ describe\ daemonsets\' --wraps='kubectl describe daemonsets' --description 'alias kdsds=kubectl describe daemonsets'
  kubectl describe daemonsets $argv; 
end
