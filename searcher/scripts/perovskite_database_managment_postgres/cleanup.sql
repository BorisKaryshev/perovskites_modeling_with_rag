-- PostgreSQL 15+. Run against the perovskites database as its owner:
-- psql -h postgres.g -U perovskites -d perovskites -X \
--   -f scripts/perovskite_database_managment_postgres/cleanup.sql
-- Removes all model v2.1 data and restarts generated IDs. Tables and schema remain.
\set ON_ERROR_STOP on

BEGIN;

TRUNCATE TABLE
    perovskite.layer,
    perovskite.property,
    perovskite.additive,
    perovskite.ion,
    perovskite.structure,
    perovskite.compound,
    perovskite.layer_stack,
    perovskite.perovskite,
    perovskite.dataset
RESTART IDENTITY CASCADE;

COMMIT;

\echo 'Removed all model v2.1 data; tables and schema remain.'
