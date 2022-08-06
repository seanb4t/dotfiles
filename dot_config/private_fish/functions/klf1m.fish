function klf1m --wraps=\'kubectl\ logs\ --since\ 1m\ -f\' --wraps='kubectl logs --since 1m -f' --description 'alias klf1m=kubectl logs --since 1m -f'
  kubectl logs --since 1m -f $argv; 
end
