function kgpall --wraps=\'kubectl\ get\ pods\ --all-namespaces\ -o\ wide\' --wraps='kubectl get pods --all-namespaces -o wide' --description 'alias kgpall=kubectl get pods --all-namespaces -o wide'
  kubectl get pods --all-namespaces -o wide $argv; 
end
