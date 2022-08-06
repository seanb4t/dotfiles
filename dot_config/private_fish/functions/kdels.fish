function kdels --wraps=\'kubectl\ delete\ svc\' --wraps='kubectl delete svc' --description 'alias kdels=kubectl delete svc'
  kubectl delete svc $argv; 
end
