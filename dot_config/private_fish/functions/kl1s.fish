function kl1s --wraps=\'kubectl\ logs\ --since\ 1s\' --wraps='kubectl logs --since 1s' --description 'alias kl1s=kubectl logs --since 1s'
  kubectl logs --since 1s $argv; 
end
