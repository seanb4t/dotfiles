function kecj --wraps=\'kubectl\ edit\ cronjob\' --wraps='kubectl edit cronjob' --description 'alias kecj=kubectl edit cronjob'
  kubectl edit cronjob $argv; 
end
