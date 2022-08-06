function krsd --wraps=\'kubectl\ rollout\ status\ deployment\' --wraps='kubectl rollout status deployment' --description 'alias krsd=kubectl rollout status deployment'
  kubectl rollout status deployment $argv; 
end
