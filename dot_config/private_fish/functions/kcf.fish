function kcf --wraps=\'kubectl\ create\ -f\' --wraps='kubectl create -f' --description 'alias kcf=kubectl create -f'
  kubectl create -f $argv; 
end
