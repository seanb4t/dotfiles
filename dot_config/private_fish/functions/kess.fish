function kess --wraps=\'kubectl\ edit\ statefulset\' --wraps='kubectl edit statefulset' --description 'alias kess=kubectl edit statefulset'
  kubectl edit statefulset $argv; 
end
