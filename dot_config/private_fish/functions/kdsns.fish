function kdsns --wraps=\'kubectl\ describe\ namespaces\' --wraps='kubectl describe namespaces' --description 'alias kdsns=kubectl describe namespaces'
  kubectl describe namespaces $argv; 
end
