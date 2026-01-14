-- a script to create the celeb connect user and the database

DROP USER IF EXISTS 'Celeb'@'localhost';
CREATE USER IF NOT EXISTS 'Celeb'@'localhost' IDENTIFIED BY 'celeb_connect_password';
DROP DATABASE IF EXISTS celeb_connect;
CREATE DATABASE IF NOT EXISTS celeb_connect;
GRANT ALL ON celeb_connect.* TO 'Celeb'@'localhost';
GRANT SELECT ON performance_schema.* TO "Celeb"@"localhost";
