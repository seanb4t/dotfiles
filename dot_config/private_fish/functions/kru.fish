function kru --wraps=\'kubectl\ rollout\ undo\' --wraps='kubectl rollout undo' --description 'alias kru=kubectl rollout undo'
  kubectl rollout undo $argv; 
end
