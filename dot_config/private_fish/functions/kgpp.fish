function kgpp --wraps=\'kubectl\ get\ podpreset\' --wraps='kubectl get podpreset' --description 'alias kgpp=kubectl get podpreset'
  kubectl get podpreset $argv; 
end
