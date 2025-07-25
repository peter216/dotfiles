#!/usr/bin/bash

# Check if jq is already installed
if command -v jq &> /dev/null
then
    echo "jq is already installed"
    exit 0
fi

# Check if we are on Windows
if [[ "$(uname -s)" == MINGW* ]]; then
  echo "Running on Windows"
else
  echo "Not running on Windows"
  exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null
then
    echo "curl could not be found, please install it first"
    exit 1
fi

curl -k -L -O https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe

if [ $? -ne 0 ]; then
    echo "Failed to download jq"
    exit 1
fi

HASH=$(certutil -hashfile jq-windows-amd64.exe SHA256 | tail +2 | head -1 | tr -d ' ')
EXPECTED_HASH="7451fbbf37feffb9bf262bd97c54f0da558c63f0748e64152dd87b0a07b6d6ab"
if [ "$HASH" != "$EXPECTED_HASH" ]; then
    echo "Hash mismatch! jq may be corrupted."
    exit 1
fi

mkdir -p $HOME/executables && mv -v jq-windows-amd64.exe $HOME/executables/
mkdir -p $HOME/bin && ln -s $HOME/executables/jq-windows-amd64.exe $HOME/bin/jq

# Check if jq is in PATH
if command -v jq &> /dev/null
then
    echo "jq is in PATH"
else
    echo "jq not in PATH, adding $HOME/bin to PATH"
    echo "export PATH=\$PATH:$HOME/bin" >> ~/.bashrc
    export PATH=$PATH:$HOME/bin # Add to current session
fi

# Check jq version
jq --version
if [ $? -ne 0 ]; then
    echo "jq installation failed"
    exit 1
fi
echo "jq installed successfully"

# jq
# winget jq
# winget search jq
# winget install jqlang.jq
# curl -O https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
# curl -k -O https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
# ./jq-windows-amd64.exe
# mkdir -p ~/executables; mv jq-windows-amd64.exe ~/executables/
# mkdir -p ~/bin; ln -s ~/executables/jq-windows-amd64.exe ~/bin/jq
# jq -v
# jq --version
# jq --help
# jq -h
# cat context.json | jq
# ll ~/bin
# ll ~/executables/
# cat ~/executables/jq-windows-amd64.exe
# ll jq-windows-amd64.exe
# mv jq-windows-amd64.exe ~/executables/
# ll ~/bin
# rm ~/bin/jq
# ll ~/executables/
# ln -s ~/executables/jq-windows-amd64.exe ~/bin/jq
# jq --version
# curl -O https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
# curl -k -O https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
# ll
# wget https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
# history
# curl -k -O -vvv https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
# curl --help
# curl -k -L -O -vvv https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
# ll
# rm jq-windows-amd64.exe
# curl -k -L -O https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
# ll jq-windows-amd64.exe
# md5sum.exe jq-windows-amd64.exe
# certutil
# certutil -hashfile jq-windows-amd64.exe SHA256
# history
