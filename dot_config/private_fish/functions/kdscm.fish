function kdscm --wraps=\'kubectl\ describe\ configmaps\' --wraps='kubectl describe configmaps' --description 'alias kdscm=kubectl describe configmaps'
  kubectl describe configmaps $argv; 
end
