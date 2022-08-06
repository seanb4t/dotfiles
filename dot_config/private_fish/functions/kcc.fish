function kcc --wraps=\'kubectl\ config\ get-contexts\' --wraps='kubectl config get-contexts' --description 'alias kcc=kubectl config get-contexts'
  kubectl config get-contexts $argv; 
end
