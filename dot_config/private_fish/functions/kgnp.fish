function kgnp --wraps=\'kubectl\ get\ networkpolicies\' --wraps='kubectl get networkpolicies' --description 'alias kgnp=kubectl get networkpolicies'
  kubectl get networkpolicies $argv; 
end
