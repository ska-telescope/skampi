#!/bin/bash

echo "Adding databases to MariaDB"
echo "Adding HDB++..."
mysql -u root < create_hdbpp.sql

