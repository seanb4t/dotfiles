function kgcw --wraps=\'watch\ kubectl\ get\ cronjobs\' --wraps='watch kubectl get cronjobs' --description 'alias kgcw=watch kubectl get cronjobs'
  watch kubectl get cronjobs $argv; 
end
