function klf1h --wraps=\'kubectl\ logs\ --since\ 1h\ -f\' --wraps='kubectl logs --since 1h -f' --description 'alias klf1h=kubectl logs --since 1h -f'
  kubectl logs --since 1h -f $argv; 
end
