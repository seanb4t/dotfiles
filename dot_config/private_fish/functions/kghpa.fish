function kghpa --wraps=\'kubectl\ get\ horizontalpodautoscalers\' --wraps='kubectl get horizontalpodautoscalers' --description 'alias kghpa=kubectl get horizontalpodautoscalers'
  kubectl get horizontalpodautoscalers $argv; 
end
