function kdeli --wraps=\'kubectl\ delete\ ingress\' --wraps='kubectl delete ingress' --description 'alias kdeli=kubectl delete ingress'
  kubectl delete ingress $argv; 
end
