function kcuc --wraps=\'kubectl\ config\ use-context\' --wraps='kubectl config use-context' --description 'alias kcuc=kubectl config use-context'
  kubectl config use-context $argv; 
end
