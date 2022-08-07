function opl --wraps=op --description 'local op'
set -u OP_CONNECT_HOST 
set -u OP_CONNECT_TOKEN 
op $argv
end
