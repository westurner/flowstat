#!/bin/sh
# See: http://river.styx.org/ww/2010/10/pyodbc-spasql/index

sudo apt-get install unixodbc-dev

cd $VIRTUAL_ENV/src
mkdir pyodbc
cd pyodbc

wget http://pyodbc.googlecode.com/files/pyodbc-2.1.8.zip
wget http://river.styx.org/ww/2010/10/pyodbc-spasql/pyodbc-spasql-datesupport.diff

unzip pyodbc-2.1.8.zip

cd pyodbc-2.1.8
patch -p1 < ../pyodbc-spasql-datesupport.diff
python setup.py install
