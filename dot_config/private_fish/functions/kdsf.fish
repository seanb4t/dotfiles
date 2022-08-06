function kdsf --wraps=\'kubectl\ describe\ -f\' --wraps='kubectl describe -f' --description 'alias kdsf=kubectl describe -f'
  kubectl describe -f $argv; 
end
