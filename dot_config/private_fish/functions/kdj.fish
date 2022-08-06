function kdj --wraps=\'kubectl\ delete\ job\' --wraps='kubectl delete job' --description 'alias kdj=kubectl delete job'
  kubectl delete job $argv; 
end
