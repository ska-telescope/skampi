#!/bin/bash

app_path=$(realpath app)
mysql_script_path="${app_path}/data/createHdbppMysql.sql"
echo $mysql_script_path

# Provide archiver database name as a comand line argument
echo "Creating the archiver database and HDB++ Schema ...."

mysql -h 192.168.93.137 -u eda_admin -p@v3ng3rs@ss3mbl3 -e "CREATE DATABASE IF NOT EXISTS $1;
USE $1;
ALTER DATABASE $1 CHARACTER SET latin1 COLLATE latin1_swedish_ci;
source $mysql_script_path;
"

echo "HDB++ Schema is created."
