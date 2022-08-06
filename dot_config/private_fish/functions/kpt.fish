function kpt --wraps=\'kubectl\ get\ podtemplates\' --wraps='kubectl get podtemplates' --description 'alias kpt=kubectl get podtemplates'
  kubectl get podtemplates $argv; 
end
