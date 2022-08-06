function kdi --wraps=\'kubectl\ delete\ ingress\' --wraps='kubectl delete ingress' --description 'alias kdi=kubectl delete ingress'
  kubectl delete ingress $argv; 
end
