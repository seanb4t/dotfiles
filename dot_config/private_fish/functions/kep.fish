function kep --wraps=\'kubectl\ edit\ pods\' --wraps='kubectl edit pods' --description 'alias kep=kubectl edit pods'
  kubectl edit pods $argv; 
end
