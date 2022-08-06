function kdsp --wraps=\'kubectl\ describe\ pods\' --wraps='kubectl describe pods' --description 'alias kdsp=kubectl describe pods'
  kubectl describe pods $argv; 
end
