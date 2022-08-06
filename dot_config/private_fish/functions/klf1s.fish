function klf1s --wraps=\'kubectl\ logs\ --since\ 1s\ -f\' --wraps='kubectl logs --since 1s -f' --description 'alias klf1s=kubectl logs --since 1s -f'
  kubectl logs --since 1s -f $argv; 
end
