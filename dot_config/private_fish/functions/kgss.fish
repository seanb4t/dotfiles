function kgss --wraps=\'kubectl\ get\ statefulsets\' --wraps='kubectl get statefulsets' --description 'alias kgss=kubectl get statefulsets'
  kubectl get statefulsets $argv; 
end
