"""Agent tools for the version 2.1 perovskite PostgreSQL model."""

from __future__ import annotations

import json
import os
import logging

import psycopg
from src.perovskite_models import PerovskiteData
from src.perovskite_models.dba import DBA

from .decorator import tool

logger = logging.getLogger(__name__)


def _log_database_target(dsn: str) -> None:
    """Log connection context without passwords or the raw connection string."""
    try:
        options = psycopg.conninfo.conninfo_to_dict(dsn)
    except psycopg.Error:
        logger.warning("Invalid PostgreSQL connection string; target unavailable")
        return
    target = {key: options.get(key) or os.environ.get(env) or "libpq default"
              for key, env in (("host", "PGHOST"), ("port", "PGPORT"),
                               ("dbname", "PGDATABASE"), ("user", "PGUSER"))}
    logger.info("PostgreSQL connection target: %s", target)


MODEL_VERSION = "2.1"
PEROVSKITE_SEARCH_FIELDS = tuple(DBA._perovskite_search)
LAYER_STACK_SEARCH_FIELDS = tuple(DBA._stack_search)
_database_dsn: str | None = None


def configure_perovskite_database(dsn: str) -> None:
    """Set the PostgreSQL DSN used by the tools in this process."""
    global _database_dsn
    if not dsn or not dsn.strip():
        raise ValueError("The perovskite database DSN cannot be empty")
    _database_dsn = dsn.strip()


def get_perovskite_model_schema() -> dict:
    """Return the exact Pydantic/JSON schema used by the add tool."""
    return PerovskiteData.model_json_schema()


def _dsn() -> str:
    value = _database_dsn or os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "Perovskite database is not configured. Set [perovskite_database] "
            "dsn in the config or export DATABASE_URL."
        )
    _log_database_target(value)
    return value


def _json_result(**values) -> str:
    return json.dumps(values, ensure_ascii=False, indent=2)


def _parse_filters(filters_json: str, allowed: tuple[str, ...]) -> dict[str, str]:
    try:
        filters = json.loads(filters_json)
    except json.JSONDecodeError as ex:
        raise ValueError(f"filters_json is not valid JSON: {ex.msg}") from ex
    if not isinstance(filters, dict):
        raise ValueError("filters_json must contain one JSON object")
    unknown = set(filters) - set(allowed)
    if unknown:
        raise ValueError(
            "Unknown search fields: " + ", ".join(sorted(unknown))
        )
    if any(not isinstance(value, str) for value in filters.values()):
        raise ValueError("Every search pattern must be a string")
    return filters


@tool
def add_perovskite_structure(document: dict) -> str:
    """Validate and add one perovskite model v2.1 dataset to PostgreSQL.

    `document` must be a JSON object matching PerovskiteData with root arrays
    `perovskites` and `layer_stacks`. Unknown facts must be omitted or null, never
    guessed. Material properties belong to a perovskite; photovoltaic metrics such
    as pce, voc, jsc, fill_factor and eqe belong to a layer stack. The return value
    includes the generated dataset_id needed to retrieve or delete the dataset.
    """
    logger.info("Validating perovskite dataset for insertion")
    data = PerovskiteData.model_validate(document)
    if not data.perovskites and not data.layer_stacks:
        raise ValueError("Refusing to add an empty PerovskiteData dataset")
    dataset_id = DBA(_dsn()).save(data)
    logger.info("Saved dataset_id=%s perovskites=%d layer_stacks=%d",
                dataset_id, len(data.perovskites), len(data.layer_stacks))
    return _json_result(
        ok=True,
        model_version=MODEL_VERSION,
        dataset_id=dataset_id,
        perovskites=len(data.perovskites),
        layer_stacks=len(data.layer_stacks),
    )


# Expose the complete model to the LLM. In particular, `document` is a native
# object rather than JSON serialized into a second string layer.
add_perovskite_structure._tool_schema["function"]["parameters"] = {
    "type": "object",
    "properties": {"document": get_perovskite_model_schema()},
    "required": ["document"],
    "additionalProperties": False,
}


@tool
def delete_perovskite_structure(dataset_id: int, confirmation: str) -> str:
    """Delete one complete perovskite dataset by its database dataset_id.

    This cascades to every material, structure, compound, layer, and property in
    the dataset. Only call after the user explicitly approves that exact ID. Pass
    confirmation exactly as `DELETE DATASET <dataset_id>`; otherwise nothing is
    changed.
    """
    expected = f"DELETE DATASET {dataset_id}"
    logger.info("Deleting dataset_id=%s", dataset_id)
    if confirmation != expected:
        logger.warning("Deletion refused: confirmation mismatch dataset_id=%s", dataset_id)
        return _json_result(
            ok=False,
            deleted=False,
            dataset_id=dataset_id,
            error=f"Confirmation must be exactly: {expected}",
        )
    db = DBA(_dsn())
    existing = db.get(dataset_id)
    if existing is None:
        logger.warning("Deletion skipped: dataset_id=%s not found", dataset_id)
        return _json_result(
            ok=False,
            deleted=False,
            dataset_id=dataset_id,
            error="Dataset not found",
        )
    deleted = db.delete(dataset_id)
    logger.info("Deletion result dataset_id=%s deleted=%s", dataset_id, deleted)
    return _json_result(
        ok=deleted,
        deleted=deleted,
        dataset_id=dataset_id,
        perovskites=len(existing.perovskites),
        layer_stacks=len(existing.layer_stacks),
    )


@tool
def search_perovskite_structures(
    entity: str, filters_json: str, limit: int = 20
) -> str:
    """Search perovskite model v2.1 records using AND-combined regex fields.

    Set entity to `perovskite` or `layer_stack`. `filters_json` is a JSON object;
    values are case-insensitive PostgreSQL regular expressions. An empty object
    lists records. Perovskite fields: id, formula, source, notes,
    structure.family, structure.space_group, structure.dimensionality,
    structure.cif, ions.site, ions.coefficient, ions.compound.name,
    ions.compound.formula, ions.compound.smiles, ions.compound.iupac_name,
    ions.compound.cas_number, ions.compound.source_compound, additives.amount,
    additives.unit, additives.basis, additives.compound.<compound field>,
    impurities.amount, impurities.unit, impurities.basis,
    impurities.compound.<compound field>, properties.name, properties.value,
    properties.unit, properties.method, properties.conditions, properties.source.
    Layer-stack fields: architecture, layers.material, layers.perovskite_id,
    layers.thickness_nm, and all properties.<property field> fields above.
    Each result includes dataset_id so it can be traced or deleted.
    """
    logger.info("Searching entity=%s filters=%s limit=%s", entity, filters_json, limit)
    if entity not in {"perovskite", "layer_stack"}:
        raise ValueError("entity must be 'perovskite' or 'layer_stack'")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    db = DBA(_dsn())
    if entity == "perovskite":
        allowed = PEROVSKITE_SEARCH_FIELDS
        patterns = _parse_filters(filters_json, allowed)
        root, id_column, mapping = (
            "perovskite.perovskite p",
            "p.id",
            DBA._perovskite_search,
        )
    else:
        allowed = LAYER_STACK_SEARCH_FIELDS
        patterns = _parse_filters(filters_json, allowed)
        root, id_column, mapping = (
            "perovskite.layer_stack ls",
            "ls.id",
            DBA._stack_search,
        )

    results = []
    with psycopg.connect(db.dsn) as connection:
        logger.info("PostgreSQL connected; executing %s search", entity)
        matching_ids = db._search_ids(
            connection, root, id_column, mapping, patterns
        )
        row_ids = matching_ids[:limit]
        for (row_id,) in row_ids:
            if entity == "perovskite":
                dataset_id = connection.execute(
                    "SELECT dataset_id FROM perovskite.perovskite WHERE id = %s",
                    (row_id,),
                ).fetchone()[0]
                item = db._load_perovskite(connection, row_id)
            else:
                dataset_id = connection.execute(
                    "SELECT dataset_id FROM perovskite.layer_stack WHERE id = %s",
                    (row_id,),
                ).fetchone()[0]
                item = db._load_stack(connection, row_id)
            results.append(
                {
                    "dataset_id": dataset_id,
                    "entity": entity,
                    "data": item.model_dump(mode="json", exclude_none=True),
                }
            )

    logger.info("Search complete entity=%s matched=%d returned=%d truncated=%s",
                entity, len(matching_ids), len(results), len(matching_ids) > limit)
    return _json_result(
        ok=True,
        model_version=MODEL_VERSION,
        entity=entity,
        filters=patterns,
        count=len(results),
        truncated=len(matching_ids) > limit,
        results=results,
    )


__all__ = [
    "MODEL_VERSION",
    "PEROVSKITE_SEARCH_FIELDS",
    "LAYER_STACK_SEARCH_FIELDS",
    "add_perovskite_structure",
    "configure_perovskite_database",
    "delete_perovskite_structure",
    "get_perovskite_model_schema",
    "search_perovskite_structures",
]
