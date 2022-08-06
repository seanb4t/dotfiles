function kef --wraps=\'kubectl\ edit\ -f\' --wraps='kubectl edit -f' --description 'alias kef=kubectl edit -f'
  kubectl edit -f $argv; 
end
