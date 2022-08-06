function kdd --wraps=\'kubectl\ delete\ deployment\' --wraps='kubectl delete deployment' --description 'alias kdd=kubectl delete deployment'
  kubectl delete deployment $argv; 
end
