function kcdc --wraps=\'kubectl\ config\ delete-context\' --wraps='kubectl config delete-context' --description 'alias kcdc=kubectl config delete-context'
  kubectl config delete-context $argv; 
end
