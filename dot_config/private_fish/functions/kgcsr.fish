function kgcsr --wraps=\'kubectl\ get\ certificatesigningrequests\' --wraps='kubectl get certificatesigningrequests' --description 'alias kgcsr=kubectl get certificatesigningrequests'
  kubectl get certificatesigningrequests $argv; 
end
