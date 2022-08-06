function krsss --wraps=\'kubectl\ rollout\ status\ statefulset\' --wraps='kubectl rollout status statefulset' --description 'alias krsss=kubectl rollout status statefulset'
  kubectl rollout status statefulset $argv; 
end
