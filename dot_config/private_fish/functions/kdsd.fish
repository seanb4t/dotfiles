function kdsd --wraps=\'kubectl\ describe\ deployments\' --wraps='kubectl describe deployments' --description 'alias kdsd=kubectl describe deployments'
  kubectl describe deployments $argv; 
end
