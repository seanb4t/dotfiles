function code-uninstall --wraps='code --uninstall-extension' --description 'alias code-uninstall=code --uninstall-extension'
  code --uninstall-extension $argv; 
end
