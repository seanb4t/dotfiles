function kgev --wraps=\'kubectl\ get\ events\' --wraps='kubectl get events' --description 'alias kgev=kubectl get events'
  kubectl get events $argv; 
end
