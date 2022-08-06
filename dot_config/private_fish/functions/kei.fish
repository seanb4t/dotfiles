function kei --wraps=\'kubectl\ edit\ ingress\' --wraps='kubectl edit ingress' --description 'alias kei=kubectl edit ingress'
  kubectl edit ingress $argv; 
end
