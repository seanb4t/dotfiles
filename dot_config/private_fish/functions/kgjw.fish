function kgjw --wraps=\'watch\ kubectl\ get\ jobs\' --wraps='watch kubectl get jobs' --description 'alias kgjw=watch kubectl get jobs'
  watch kubectl get jobs $argv; 
end
