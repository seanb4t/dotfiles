function kdelsa --wraps=\'kubectl\ delete\ sa\' --wraps='kubectl delete sa' --description 'alias kdelsa=kubectl delete sa'
  kubectl delete sa $argv; 
end
