function kpf --wraps=\'kubectl\ port-forward\' --wraps='kubectl port-forward' --description 'alias kpf=kubectl port-forward'
  kubectl port-forward $argv; 
end
