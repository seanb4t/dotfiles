function kdelp --wraps=\'kubectl\ delete\ pods\' --wraps='kubectl delete pods' --description 'alias kdelp=kubectl delete pods'
  kubectl delete pods $argv; 
end
