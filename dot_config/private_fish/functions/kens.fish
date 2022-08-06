function kens --wraps=\'kubectl\ edit\ namespaces\' --wraps='kubectl edit namespaces' --description 'alias kens=kubectl edit namespaces'
  kubectl edit namespaces $argv; 
end
