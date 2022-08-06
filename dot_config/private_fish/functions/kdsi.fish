function kdsi --wraps=\'kubectl\ describe\ ingress\' --wraps='kubectl describe ingress' --description 'alias kdsi=kubectl describe ingress'
  kubectl describe ingress $argv; 
end
