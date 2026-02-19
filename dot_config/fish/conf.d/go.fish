#!/usr/bin/env fish

# Add Go workspace bin to PATH
if test -d ~/go/bin
    fish_add_path ~/go/bin
end

# Set GOPATH if not already set (defaults to ~/go)
if not set -q GOPATH
    set -gx GOPATH ~/go
end

# Set GOBIN for installed binaries
if not set -q GOBIN
    set -gx GOBIN ~/go/bin
end
