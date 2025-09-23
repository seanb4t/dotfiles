fish_add_path /opt/homebrew/bin /opt/homebrew/sbin /home/linuxbrew/.linuxbrew/bin

if not type -q brew
  echo "Please install 'brew' first!"
  exit 0
end

brew shellenv | source

