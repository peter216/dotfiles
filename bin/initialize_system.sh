#! /usr/bin/env bash

sudo apt-get install -y gopass
sudo apt-get install -y yq
sudo apt-get install -y ncdu
sudo apt install -y btop
sudo apt -y install tree
sudo apt-get install -y chezmoi
curl -LsSf https://astral.sh/uv/install.sh | sh
mkdir tmp && cd tmp
curl -k -L -O https://nightly.link/Genivia/ugrep/workflows/autobuild-static/master/ugrep_amd64_d624720_2507021907.zip
unzip ugrep_amd64_d624720_2507021907.zip 
cp bin/ugrep ~/.local/bin/
cd .. && rm -vrf tmp
uv tool install httpie
uv tool install ipython
