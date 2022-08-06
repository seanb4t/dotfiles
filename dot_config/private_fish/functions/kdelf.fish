function kdelf --wraps=\'kubectl\ delete\ -f\' --wraps='kubectl delete -f' --description 'alias kdelf=kubectl delete -f'
  kubectl delete -f $argv; 
end
