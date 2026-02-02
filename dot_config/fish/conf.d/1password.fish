# 1password.fish
# A fish shell script to integrate 1Password CLI with fish shell

function mac_link_1password
  set -l source_socket ~/Library/Group\ Containers/2BUA8C4S2C.com.1password/t/agent.sock
  set -l dest_socket ~/.1password/agent.sock

  if test ! -e $dest_socket
    mkdir -p ~/.1password
    ln -sf $source_socket $dest_socket
  end

  set -gx SSH_AUTH_SOCK $dest_socket
end


# setup SSH_AUTH_SOCK and sign in if not on a Mac

switch (uname)
case Darwin
  mac_link_1password
case Linux
  # if interactive shell, sign in
  if status is-interactive
    eval (op signin)
  end
case '*'
  # Nothing
end

