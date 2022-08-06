function klf --wraps=\'kubectl\ logs\ -f\' --wraps='kubectl logs -f' --description 'alias klf=kubectl logs -f'
  kubectl logs -f $argv; 
end
