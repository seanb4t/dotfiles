function kgrq --wraps=\'kubectl\ get\ resourcequotas\' --wraps='kubectl get resourcequotas' --description 'alias kgrq=kubectl get resourcequotas'
  kubectl get resourcequotas $argv; 
end
