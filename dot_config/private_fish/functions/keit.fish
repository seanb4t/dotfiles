function keit --wraps=\'kubectl\ exec\ -it\ --\' --wraps='kubectl exec -it --' --description 'alias keit=kubectl exec -it --'
  kubectl exec -it -- $argv; 
end
