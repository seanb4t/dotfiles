function tfi --wraps='terraform init -upgrade' --description 'alias tfi=terraform init -upgrade'
  terraform init -upgrade $argv
        
end
