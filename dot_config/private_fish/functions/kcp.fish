function kcp --wraps=\'kubectl\ cp\' --wraps='kubectl cp' --description 'alias kcp=kubectl cp'
  kubectl cp $argv; 
end
