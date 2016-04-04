CREATE USER pks_user WITH password 'pass';
ALTER ROLE pks_user SET client_encoding TO 'utf8';
ALTER ROLE pks_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE pks_user SET timezone TO 'UTC';

CREATE DATABASE pks;
GRANT ALL PRIVILEGES ON DATABASE pks TO pks_user;
\c pks
CREATE EXTENSION IF NOT EXISTS postgis;

