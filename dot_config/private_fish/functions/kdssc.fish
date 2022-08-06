function kdssc --wraps=\'kubectl\ describe\ secrets\' --wraps='kubectl describe secrets' --description 'alias kdssc=kubectl describe secrets'
  kubectl describe secrets $argv; 
end
