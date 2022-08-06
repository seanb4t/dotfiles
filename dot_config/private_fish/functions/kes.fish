function kes --wraps=\'kubectl\ edit\ services\' --wraps='kubectl edit services' --description 'alias kes=kubectl edit services'
  kubectl edit services $argv; 
end
