function kgc --wraps=\'kubectl\ get\ cronjobs\' --wraps='kubectl get cronjobs' --description 'alias kgc=kubectl get cronjobs'
  kubectl get cronjobs $argv; 
end
