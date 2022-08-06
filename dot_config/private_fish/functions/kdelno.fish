function kdelno --wraps=\'kubectl\ delete\ node\' --wraps='kubectl delete node' --description 'alias kdelno=kubectl delete node'
  kubectl delete node $argv; 
end
