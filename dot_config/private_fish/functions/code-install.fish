function code-install --wraps='code --install-extension' --description 'alias code-install=code --install-extension'
  code --install-extension $argv; 
end
