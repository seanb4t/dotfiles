# 1password.fish
# A fish shell script to integrate 1Password CLI with fish shell

function mac_link_1password
  set -l 1password_socket ~/Library/Group\ Containers/2BUA8C4S2C.com.1password/t/agent.sock
  if test ! -L $1password_socket
    mkdir -p ~/.1password
    ln -sf $1password_socket ~/.1password/agent.sock
  end

  set -gx SSH_AUTH_SOCK ~/.1password/agent.sock
end


# setup SSH_AUTH_SOCK and sign in if not on a Mac

switch (uname)
case Darwin
  mac_link_1password
case Linux
  op signin | source
case '*'
  # Nothing
end

