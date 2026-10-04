-- PostgreSQL 15+. Normalized storage for PerovskiteData 2.1.
BEGIN;

CREATE SCHEMA IF NOT EXISTS perovskite;
SET LOCAL search_path = perovskite, pg_catalog;

CREATE TABLE dataset (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE perovskite (
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

CREATE TABLE structure (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    perovskite_id bigint NOT NULL UNIQUE REFERENCES perovskite(id) ON DELETE CASCADE,
    family text,
    space_group text,
    dimensionality smallint CHECK (dimensionality BETWEEN 0 AND 3),
    cif text
);

CREATE TABLE compound (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    dataset_id bigint NOT NULL REFERENCES dataset(id) ON DELETE CASCADE,
    name text NOT NULL CHECK (length(name) > 0),
    formula text,
    smiles text,
    iupac_name text,
    cas_number text,
    source_compound text
);

CREATE TABLE ion (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    perovskite_id bigint NOT NULL REFERENCES perovskite(id) ON DELETE CASCADE,
    position integer NOT NULL CHECK (position >= 0),
    site text NOT NULL CHECK (site IN ('A', 'B', 'X', 'spacer', 'other')),
    compound_id bigint NOT NULL UNIQUE REFERENCES compound(id) ON DELETE CASCADE,
    coefficient numeric NOT NULL CHECK (coefficient > 0),
    UNIQUE (perovskite_id, position)
);

CREATE TABLE additive (
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

CREATE TABLE layer_stack (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    dataset_id bigint NOT NULL REFERENCES dataset(id) ON DELETE CASCADE,
    position integer NOT NULL CHECK (position >= 0),
    architecture text,
    UNIQUE (dataset_id, position),
    UNIQUE (dataset_id, id)
);

CREATE TABLE layer (
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

CREATE TABLE property (
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

CREATE UNIQUE INDEX property_perovskite_position_idx
    ON property(perovskite_id, position) WHERE perovskite_id IS NOT NULL;
CREATE UNIQUE INDEX property_stack_position_idx
    ON property(layer_stack_id, position) WHERE layer_stack_id IS NOT NULL;
CREATE INDEX perovskite_formula_idx ON perovskite(formula);
CREATE INDEX compound_name_idx ON compound(name);
CREATE INDEX compound_formula_idx ON compound(formula);
CREATE INDEX compound_cas_idx ON compound(cas_number);
CREATE INDEX ion_site_idx ON ion(site);
CREATE INDEX property_name_idx ON property(name);
CREATE INDEX layer_material_idx ON layer(material);
CREATE INDEX layer_perovskite_idx ON layer(perovskite_id);

COMMIT;
