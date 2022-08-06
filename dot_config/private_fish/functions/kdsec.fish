function kdsec --wraps=\'kubectl\ describe\ secret\' --wraps='kubectl describe secret' --description 'alias kdsec=kubectl describe secret'
  kubectl describe secret $argv; 
end
