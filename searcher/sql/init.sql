-- PostgreSQL 15+. Run once with psql as a PostgreSQL administrator:
-- psql -h postgres.g -U postgres -d postgres -X -f sql/init.sql
-- Run from searcher/, or pass the full path to this file.
-- Do not use --single-transaction: CREATE DATABASE must run outside a transaction.
-- Existing roles/databases are not overwritten; errors stop the script.
\set ON_ERROR_STOP on

CREATE ROLE perovskites
    LOGIN PASSWORD 'perovskites'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;

CREATE DATABASE perovskites OWNER perovskites;

-- Keep the current server, port, and administrator credentials.
\connect perovskites

-- Create tables and identity sequences under the application's ownership.
SET ROLE perovskites;
\ir schema-v2.1.sql
RESET ROLE;

\echo 'Initialized database perovskites with login perovskites and model v2.1.'
