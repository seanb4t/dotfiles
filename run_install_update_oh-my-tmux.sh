#!/usr/bin/env fish

if test -d ~/.tmux/.git 
  and test -f ~/.tmux/.tmux.conf 

  cd ~/.tmux && git pull -q
else
  cd ~ && git clone https://github.com/gpakosz/.tmux.git 
  cd ~ && ln -s -f .tmux/.tmux.conf . 
end
