function keti --wraps=\'kubectl\ exec\ -t\ -i\' --wraps='kubectl exec -t -i' --description 'alias keti=kubectl exec -t -i'
  kubectl exec -t -i $argv; 
end
