function kgrc --wraps=\'kubectl\ get\ replicationcontrollers\' --wraps='kubectl get replicationcontrollers' --description 'alias kgrc=kubectl get replicationcontrollers'
  kubectl get replicationcontrollers $argv; 
end
