#!/bin/bash

echo "Adding databases to MariaDB"
echo "Adding HDB++..."
mysql -u root < /usr/share/libhdb++mysql/create_hdb++.sql

