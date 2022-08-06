function ked --wraps=\'kubectl\ edit\ deployments\' --wraps='kubectl edit deployments' --description 'alias ked=kubectl edit deployments'
  kubectl edit deployments $argv; 
end
