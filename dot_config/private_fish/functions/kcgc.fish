function kcgc --wraps=\'kubectl\ config\ get-contexts\' --wraps='kubectl config get-contexts' --description 'alias kcgc=kubectl config get-contexts'
  kubectl config get-contexts $argv; 
end
