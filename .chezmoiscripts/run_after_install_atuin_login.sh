#!/bin/bash

# sign in to op
eval $(op signin)

# if 'atuin status' returns a string starting with "You are not logged in to a sync server"
# then login

if [[ "$(atuin status)" == *"You are not logged in to a sync server"* ]]; then
  echo "Logging in to atuin..."
  atuin login -u "$(op read -n 'op://Private/atuin/username')" \
    -p "$(op read -n 'op://Private/atuin/password')" \
    -k "$(op read -n 'op://Private/atuin/key_base64')"
fi
