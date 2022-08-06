function kgia --wraps=\'kubectl\ get\ ingress\ --all-namespaces\' --wraps='kubectl get ingress --all-namespaces' --description 'alias kgia=kubectl get ingress --all-namespaces'
  kubectl get ingress --all-namespaces $argv; 
end
