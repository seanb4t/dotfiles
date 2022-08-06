function ktp --wraps=\'kubectl\ top\ pods\' --wraps='kubectl top pods' --description 'alias ktp=kubectl top pods'
  kubectl top pods $argv; 
end
