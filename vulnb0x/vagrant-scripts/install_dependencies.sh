#!/bin/bash

echo "~~~~~~~~~~~~~~~~ Installing docker dependencies ~~~~~~~~~~~~~~~~"
apt update
apt install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
apt update

echo "~~~~~~~~~~~~~~~~ Installing docker ~~~~~~~~~~~~~~~~"
apt install -y docker-ce docker-ce-cli containerd.io

echo "~~~~~~~~~~~~~~~~ Installing docker-compose ~~~~~~~~~~~~~~~~"
curl -L https://github.com/docker/compose/releases/download/1.25.3/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

echo "~~~~~~~~~~~~~~~ Create user Bob ~~~~~~~~~~~~~~~~~~~"
useradd -m bob
usermod -aG sudo bob