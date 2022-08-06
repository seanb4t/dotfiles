function kdelcj --wraps=\'kubectl\ delete\ cronjob\' --wraps='kubectl delete cronjob' --description 'alias kdelcj=kubectl delete cronjob'
  kubectl delete cronjob $argv; 
end
