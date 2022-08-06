function kgiy --wraps=\'kubectl\ get\ ingress\ -o\ yaml\' --wraps='kubectl get ingress -o yaml' --description 'alias kgiy=kubectl get ingress -o yaml'
  kubectl get ingress -o yaml $argv; 
end
