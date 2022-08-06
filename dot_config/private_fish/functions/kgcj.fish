function kgcj --wraps=\'kubectl\ get\ cronjob\' --wraps='kubectl get cronjob' --description 'alias kgcj=kubectl get cronjob'
  kubectl get cronjob $argv; 
end
