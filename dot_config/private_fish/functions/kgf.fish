function kgf --wraps=\'kubectl\ get\ -f\' --wraps='kubectl get -f' --description 'alias kgf=kubectl get -f'
  kubectl get -f $argv; 
end
