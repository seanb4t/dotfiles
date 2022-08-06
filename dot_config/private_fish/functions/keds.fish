function keds --wraps=\'kubectl\ edit\ daemonsets\' --wraps='kubectl edit daemonsets' --description 'alias keds=kubectl edit daemonsets'
  kubectl edit daemonsets $argv; 
end
