function kgcrd --wraps=\'kubectl\ get\ customresourcedefinition\' --wraps='kubectl get customresourcedefinition' --description 'alias kgcrd=kubectl get customresourcedefinition'
  kubectl get customresourcedefinition $argv; 
end
