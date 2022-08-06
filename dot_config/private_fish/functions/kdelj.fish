function kdelj --wraps=\'kubectl\ delete\ job\' --wraps='kubectl delete job' --description 'alias kdelj=kubectl delete job'
  kubectl delete job $argv; 
end
