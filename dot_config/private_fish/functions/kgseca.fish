function kgseca --wraps=\'kubectl\ get\ secret\ --all-namespaces\' --wraps='kubectl get secret --all-namespaces' --description 'alias kgseca=kubectl get secret --all-namespaces'
  kubectl get secret --all-namespaces $argv; 
end
