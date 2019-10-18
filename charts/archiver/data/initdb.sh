#!/bin/bash

echo "Adding databases to MariaDB"
echo "Adding HDB++..."
mysql -u root < /data/create_hdbpp.sql

