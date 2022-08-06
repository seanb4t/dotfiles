function kgrb --wraps=\'kubectl\ get\ rolebindings\' --wraps='kubectl get rolebindings' --description 'alias kgrb=kubectl get rolebindings'
  kubectl get rolebindings $argv; 
end
