function ls --wraps=l --wraps='exa $EXA_STANDARD_OPTIONS $EXA_LS_OPTIONS' --description 'alias ls exa $EXA_STANDARD_OPTIONS $EXA_LS_OPTIONS'
  exa $EXA_STANDARD_OPTIONS $EXA_LS_OPTIONS $argv; 
end
