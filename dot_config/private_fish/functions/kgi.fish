function kgi --wraps=\'kubectl\ get\ ingress\' --wraps='kubectl get ingress' --description 'alias kgi=kubectl get ingress'
  kubectl get ingress $argv; 
end
