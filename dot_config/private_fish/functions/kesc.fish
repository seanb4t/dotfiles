function kesc --wraps=\'kubectl\ edit\ secrets\' --wraps='kubectl edit secrets' --description 'alias kesc=kubectl edit secrets'
  kubectl edit secrets $argv; 
end
