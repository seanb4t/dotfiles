function kec --wraps=\'kubectl\ edit\ cronjobs\' --wraps='kubectl edit cronjobs' --description 'alias kec=kubectl edit cronjobs'
  kubectl edit cronjobs $argv; 
end
