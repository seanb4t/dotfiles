function kdc --wraps=\'kubectl\ delete\ cronjobs\' --wraps='kubectl delete cronjobs' --description 'alias kdc=kubectl delete cronjobs'
  kubectl delete cronjobs $argv; 
end
