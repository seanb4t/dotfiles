function kgcs --wraps=\'kubectl\ get\ componentstatus\' --wraps='kubectl get componentstatus' --description 'alias kgcs=kubectl get componentstatus'
  kubectl get componentstatus $argv; 
end
