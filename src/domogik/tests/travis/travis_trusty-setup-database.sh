#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

mysql -u root -e 'create database domogik;'
echo "USE mysql;\nUPDATE user SET password=PASSWORD('domopass') WHERE user='travis@localhost';\nFLUSH PRIVILEGES;\n" | mysql -u root
echo "USE mysql;\nGRANT ALL PRIVILEGES ON domogik.* TO travis@localhost;\n" | mysql -u root


