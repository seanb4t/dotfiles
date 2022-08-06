function kgpw --wraps=\'watch\ kubectl\ get\ pods\' --wraps='watch kubectl get pods' --description 'alias kgpw=watch kubectl get pods'
  watch kubectl get pods $argv; 
end
