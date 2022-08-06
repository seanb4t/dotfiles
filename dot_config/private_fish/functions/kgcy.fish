function kgcy --wraps=\'kubectl\ get\ cronjobs\ -o\ yaml\' --wraps='kubectl get cronjobs -o yaml' --description 'alias kgcy=kubectl get cronjobs -o yaml'
  kubectl get cronjobs -o yaml $argv; 
end
