function kgssa --wraps=\'kubectl\ get\ statefulset\ --all-namespaces\' --wraps='kubectl get statefulset --all-namespaces' --description 'alias kgssa=kubectl get statefulset --all-namespaces'
  kubectl get statefulset --all-namespaces $argv; 
end
