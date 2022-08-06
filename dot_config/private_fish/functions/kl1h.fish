function kl1h --wraps=\'kubectl\ logs\ --since\ 1h\' --wraps='kubectl logs --since 1h' --description 'alias kl1h=kubectl logs --since 1h'
  kubectl logs --since 1h $argv; 
end
