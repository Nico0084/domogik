#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

wget http://dev.mysql.com/get/mysql-apt-config_0.6.0-1_all.deb
sudo dpkg -i mysql-apt-config_0.6.0-1_all.deb
sudo apt-get update -q
sudo apt-get install -q -y mysql-server
