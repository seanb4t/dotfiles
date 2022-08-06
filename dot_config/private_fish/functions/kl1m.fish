function kl1m --wraps=\'kubectl\ logs\ --since\ 1m\' --wraps='kubectl logs --since 1m' --description 'alias kl1m=kubectl logs --since 1m'
  kubectl logs --since 1m $argv; 
end
