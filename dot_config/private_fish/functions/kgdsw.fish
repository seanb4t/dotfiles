function kgdsw --wraps=\'watch\ kubectl\ get\ daemonsets\' --wraps='watch kubectl get daemonsets' --description 'alias kgdsw=watch kubectl get daemonsets'
  watch kubectl get daemonsets $argv; 
end
