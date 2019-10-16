CREATE DATABASE IF NOT EXISTS hdbpp;

USE hdbpp;

GRANT ALL PRIVILEGES  ON hdbpp.* TO 'root'@'localhost' IDENTIFIED BY '' WITH GRANT OPTION;

GRANT ALL ON hdbpp.* TO 'hdbpprw'@'%' IDENTIFIED BY "hdbpprw";

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

SET time_zone = "+00:00";

ALTER DATABASE hdbpp CHARACTER SET latin1 COLLATE latin1_swedish_ci;
