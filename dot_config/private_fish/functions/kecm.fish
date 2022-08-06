function kecm --wraps=\'kubectl\ edit\ configmaps\' --wraps='kubectl edit configmaps' --description 'alias kecm=kubectl edit configmaps'
  kubectl edit configmaps $argv; 
end
