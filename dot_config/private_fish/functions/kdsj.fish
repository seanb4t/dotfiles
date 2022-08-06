function kdsj --wraps=\'kubectl\ describe\ jobs\' --wraps='kubectl describe jobs' --description 'alias kdsj=kubectl describe jobs'
  kubectl describe jobs $argv; 
end
