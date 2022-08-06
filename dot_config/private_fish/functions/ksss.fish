function ksss --wraps=\'kubectl\ scale\ statefulset\' --wraps='kubectl scale statefulset' --description 'alias ksss=kubectl scale statefulset'
  kubectl scale statefulset $argv; 
end
