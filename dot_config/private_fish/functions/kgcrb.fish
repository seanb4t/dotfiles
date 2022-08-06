function kgcrb --wraps=\'kubectl\ get\ clusterrolebindings\' --wraps='kubectl get clusterrolebindings' --description 'alias kgcrb=kubectl get clusterrolebindings'
  kubectl get clusterrolebindings $argv; 
end
