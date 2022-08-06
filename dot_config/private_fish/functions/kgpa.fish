function kgpa --wraps=\'kubectl\ get\ pods\ --all-namespaces\' --wraps='kubectl get pods --all-namespaces' --description 'alias kgpa=kubectl get pods --all-namespaces'
  kubectl get pods --all-namespaces $argv; 
end
