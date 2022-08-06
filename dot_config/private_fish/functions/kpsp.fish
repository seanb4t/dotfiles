function kpsp --wraps=\'kubectl\ get\ podsecuritypolicies\' --wraps='kubectl get podsecuritypolicies' --description 'alias kpsp=kubectl get podsecuritypolicies'
  kubectl get podsecuritypolicies $argv; 
end
