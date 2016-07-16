#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

sudo apt-get update -qq
sudo apt-get install -y libzmq3-dev
pip install pyzmq
pip install argparse
sudo apt-get install -y python2.7-dev gcc
sudo apt-get install -y libssl-dev
sudo apt-get install -y libmysqlclient-dev mysql-client
pip install psycopg2
pip install docutils
#pip install python-daemon==2.0.2
#pip install netifaces
sudo apt-get install -y  python-netifaces
pip install chardet
sudo apt-get install -y mysql-server
