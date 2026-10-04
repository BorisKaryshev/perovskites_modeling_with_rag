-- PostgreSQL 15+. Run with psql as a PostgreSQL administrator:
-- psql -h postgres.g -U postgres -d postgres -X -f scripts/perovskite_database_managment_postgres/init.sql
-- Run from searcher/, or pass the full path to this file.
-- Do not use --single-transaction: CREATE DATABASE must run outside a transaction.
-- Self-contained: creates the login, database, and all v2.1 tables and indexes.
-- Safe to rerun for missing objects; does not migrate incompatible existing tables.
\set ON_ERROR_STOP on

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'perovskites') THEN
        CREATE ROLE perovskites
            LOGIN PASSWORD 'perovskites'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
    END IF;
END
$$;

-- CREATE DATABASE cannot run inside a DO block/transaction.
SELECT 'CREATE DATABASE perovskites OWNER perovskites'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'perovskites')
\gexec

GRANT CONNECT, CREATE ON DATABASE perovskites TO perovskites;

-- Keep the current server, port, and administrator credentials.
\connect perovskites

-- Create tables and identity sequences under the application's ownership.
SET ROLE perovskites;
-- PostgreSQL 15+. Normalized storage for PerovskiteData 2.1.
BEGIN;

CREATE SCHEMA IF NOT EXISTS perovskite;
SET LOCAL search_path = perovskite, pg_catalog;

CREATE TABLE IF NOT EXISTS dataset (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS perovskite (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    dataset_id bigint NOT NULL REFERENCES dataset(id) ON DELETE CASCADE,
    position integer NOT NULL CHECK (position >= 0),
    model_id text NOT NULL CHECK (length(model_id) > 0),
    formula text NOT NULL CHECK (length(formula) > 0),
    source text,
    notes text,
    UNIQUE (dataset_id, position),
    UNIQUE (dataset_id, model_id),
    UNIQUE (dataset_id, id)
);

CREATE TABLE IF NOT EXISTS structure (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    perovskite_id bigint NOT NULL UNIQUE REFERENCES perovskite(id) ON DELETE CASCADE,
    family text,
    space_group text,
    dimensionality smallint CHECK (dimensionality BETWEEN 0 AND 3),
    cif text
);

CREATE TABLE IF NOT EXISTS compound (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    dataset_id bigint NOT NULL REFERENCES dataset(id) ON DELETE CASCADE,
    name text NOT NULL CHECK (length(name) > 0),
    formula text,
    smiles text,
    iupac_name text,
    cas_number text,
    source_compound text
);

CREATE TABLE IF NOT EXISTS ion (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    perovskite_id bigint NOT NULL REFERENCES perovskite(id) ON DELETE CASCADE,
    position integer NOT NULL CHECK (position >= 0),
    site text NOT NULL CHECK (site IN ('A', 'B', 'X', 'spacer', 'other')),
    compound_id bigint NOT NULL UNIQUE REFERENCES compound(id) ON DELETE CASCADE,
    coefficient numeric NOT NULL CHECK (coefficient > 0),
    UNIQUE (perovskite_id, position)
);

CREATE TABLE IF NOT EXISTS additive (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    perovskite_id bigint NOT NULL REFERENCES perovskite(id) ON DELETE CASCADE,
    position integer NOT NULL CHECK (position >= 0),
    kind text NOT NULL CHECK (kind IN ('additive', 'impurity')),
    compound_id bigint NOT NULL UNIQUE REFERENCES compound(id) ON DELETE CASCADE,
    amount numeric CHECK (amount >= 0),
    unit text,
    basis text,
    CHECK (amount IS NULL OR (unit IS NOT NULL AND basis IS NOT NULL
                              AND length(unit) > 0 AND length(basis) > 0)),
    UNIQUE (perovskite_id, kind, position)
);

CREATE TABLE IF NOT EXISTS layer_stack (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    dataset_id bigint NOT NULL REFERENCES dataset(id) ON DELETE CASCADE,
    position integer NOT NULL CHECK (position >= 0),
    architecture text,
    UNIQUE (dataset_id, position),
    UNIQUE (dataset_id, id)
);

CREATE TABLE IF NOT EXISTS layer (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    dataset_id bigint NOT NULL,
    layer_stack_id bigint NOT NULL,
    position integer NOT NULL CHECK (position >= 0),
    material text NOT NULL CHECK (length(material) > 0),
    perovskite_id bigint,
    thickness_nm numeric CHECK (thickness_nm > 0),
    FOREIGN KEY (dataset_id, layer_stack_id)
        REFERENCES layer_stack(dataset_id, id) ON DELETE CASCADE,
    FOREIGN KEY (dataset_id, perovskite_id)
        REFERENCES perovskite(dataset_id, id) ON DELETE SET NULL (perovskite_id),
    UNIQUE (layer_stack_id, position)
);

CREATE TABLE IF NOT EXISTS property (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    dataset_id bigint NOT NULL REFERENCES dataset(id) ON DELETE CASCADE,
    perovskite_id bigint,
    layer_stack_id bigint,
    position integer NOT NULL CHECK (position >= 0),
    name text NOT NULL CHECK (length(name) > 0),
    value numeric NOT NULL,
    unit text NOT NULL CHECK (length(unit) > 0),
    method text,
    conditions text,
    source text,
    FOREIGN KEY (dataset_id, perovskite_id)
        REFERENCES perovskite(dataset_id, id) ON DELETE CASCADE,
    FOREIGN KEY (dataset_id, layer_stack_id)
        REFERENCES layer_stack(dataset_id, id) ON DELETE CASCADE,
    CHECK (num_nonnulls(perovskite_id, layer_stack_id) = 1),
    CHECK (perovskite_id IS NULL OR lower(name) NOT IN
           ('pce', 'voc', 'jsc', 'fill_factor', 'eqe'))
);

CREATE UNIQUE INDEX IF NOT EXISTS property_perovskite_position_idx
    ON property(perovskite_id, position) WHERE perovskite_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS property_stack_position_idx
    ON property(layer_stack_id, position) WHERE layer_stack_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS perovskite_formula_idx ON perovskite(formula);
CREATE INDEX IF NOT EXISTS compound_name_idx ON compound(name);
CREATE INDEX IF NOT EXISTS compound_formula_idx ON compound(formula);
CREATE INDEX IF NOT EXISTS compound_cas_idx ON compound(cas_number);
CREATE INDEX IF NOT EXISTS ion_site_idx ON ion(site);
CREATE INDEX IF NOT EXISTS property_name_idx ON property(name);
CREATE INDEX IF NOT EXISTS layer_material_idx ON layer(material);
CREATE INDEX IF NOT EXISTS layer_perovskite_idx ON layer(perovskite_id);

COMMIT;
RESET ROLE;

\echo 'Initialized database perovskites with login perovskites and model v2.1.'
