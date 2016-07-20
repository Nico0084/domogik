#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

sudo dpkg -P mysql
wget http://repo.mysql.com//mysql-apt-config_0.7.3-1_all.deb
sudo dpkg -i mysql-apt-config_0.7.3-1_all.deb
sudo apt-get update -q
sudo apt-get install -y mysql-server
