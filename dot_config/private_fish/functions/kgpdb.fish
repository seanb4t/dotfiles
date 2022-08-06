function kgpdb --wraps=\'kubectl\ get\ poddisruptionbudgets\' --wraps='kubectl get poddisruptionbudgets' --description 'alias kgpdb=kubectl get poddisruptionbudgets'
  kubectl get poddisruptionbudgets $argv; 
end
