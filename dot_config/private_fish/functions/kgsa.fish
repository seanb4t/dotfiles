function kgsa --wraps=\'kubectl\ get\ serviceaccounts\' --wraps='kubectl get serviceaccounts' --description 'alias kgsa=kubectl get serviceaccounts'
  kubectl get serviceaccounts $argv; 
end
