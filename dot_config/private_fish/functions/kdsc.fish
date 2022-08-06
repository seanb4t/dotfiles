function kdsc --wraps=\'kubectl\ describe\ cronjobs\' --wraps='kubectl describe cronjobs' --description 'alias kdsc=kubectl describe cronjobs'
  kubectl describe cronjobs $argv; 
end
