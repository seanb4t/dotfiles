function kglr --wraps=\'kubectl\ get\ limitranges\' --wraps='kubectl get limitranges' --description 'alias kglr=kubectl get limitranges'
  kubectl get limitranges $argv; 
end
