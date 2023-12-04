# 00_universal-pre-config.fish

if type -q grc
  if not contains "ls" $grc_plugin_ignore_execs
    set -Ua grc_plugin_ignore_execs "ls"
  end
end
