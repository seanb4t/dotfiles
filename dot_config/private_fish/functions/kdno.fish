function kdno --wraps=\'kubectl\ describe\ node\' --wraps='kubectl describe node' --description 'alias kdno=kubectl describe node'
  kubectl describe node $argv; 
end
