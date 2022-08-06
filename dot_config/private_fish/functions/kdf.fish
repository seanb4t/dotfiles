function kdf --wraps=\'kubectl\ delete\ -f\' --wraps='kubectl delete -f' --description 'alias kdf=kubectl delete -f'
  kubectl delete -f $argv; 
end
