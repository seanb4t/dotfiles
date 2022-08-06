function ksd --wraps=\'kubectl\ scale\ deployment\' --wraps='kubectl scale deployment' --description 'alias ksd=kubectl scale deployment'
  kubectl scale deployment $argv; 
end
