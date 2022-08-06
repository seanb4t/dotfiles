function kdcj --wraps=\'kubectl\ describe\ cronjob\' --wraps='kubectl describe cronjob' --description 'alias kdcj=kubectl describe cronjob'
  kubectl describe cronjob $argv; 
end
