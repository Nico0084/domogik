#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo mysql-apt-config mysql-apt-config/enable-repo select mysql-5.7-dmr | sudo debconf-set-selections
wget http://cdn.mysql.com//Downloads/MySQL-5.7/mysql-common_5.7.13-1ubuntu14.04_amd64.deb
sudo dpkg --install mysql-common_5.7.13-1ubuntu14.04_amd64.deb
sudo apt-get update -q
sudo apt-get install -q -y -o Dpkg::Options::=--force-confnew mysql-server=5.7.13-1ubuntu14.04
