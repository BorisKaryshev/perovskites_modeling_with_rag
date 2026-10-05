"""Agent tools for the version 2.1 perovskite PostgreSQL model."""

from __future__ import annotations

import json
import os
import logging
from copy import deepcopy

import psycopg
from pydantic import ValidationError
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
def list_registered_property_names() -> str:
    """List property names currently stored in the perovskite database.

    Returns each exact registered name, its usage count, and whether it occurs
    on a material or a layer stack. Use these exact names to build property-name
    search filters; for example, band gap may be stored as `band_gap`.
    """
    dsn = _dsn()
    query = """
        SELECT name,
               count(*) AS occurrences,
               bool_or(perovskite_id IS NOT NULL) AS on_perovskite,
               bool_or(layer_stack_id IS NOT NULL) AS on_layer_stack
        FROM perovskite.property
        GROUP BY name
        ORDER BY lower(name), name
    """
    logger.info("Listing registered property names")
    with psycopg.connect(dsn) as connection:
        rows = connection.execute(query).fetchall()
    properties = [
        {
            "name": name,
            "occurrences": occurrences,
            "on_perovskite": on_perovskite,
            "on_layer_stack": on_layer_stack,
        }
        for name, occurrences, on_perovskite, on_layer_stack in rows
    ]
    logger.info("Found %d registered property names", len(properties))
    return _json_result(count=len(properties), properties=properties)


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
    try:
        data = PerovskiteData.model_validate(document)
    except ValidationError as ex:
        raise ValueError(
            "Document does not match PerovskiteData v2.1. Every perovskite "
            "requires `id`, `formula`, and `ions`. `ions` must be an array of "
            "objects shaped as {site, compound: {name, ...}, coefficient}; never "
            "use a `composition` key or a formula string for `ions`. Validation "
            f"details:\n{ex}"
        ) from ex
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
_document_schema = get_perovskite_model_schema()
_document_definitions = _document_schema.pop("$defs", {})
add_perovskite_structure._tool_schema["function"]["parameters"] = {
    "type": "object",
    "$defs": _document_definitions,
    "properties": {"document": _document_schema},
    "required": ["document"],
    "additionalProperties": False,
}
# `$ref` values generated by Pydantic start at `#/$defs/...`, so definitions
# must live at this parameters object's root rather than inside `document`.


def make_pdf_add_perovskite_tool(source_path: str):
    """Bind PDF provenance in code so the model cannot omit or alter it."""
    absolute_source = os.path.abspath(source_path)

    @tool
    def add_pdf_perovskite_structure(document: dict) -> str:
        """Add perovskite data extracted from the current PDF."""
        prepared_document = deepcopy(document)
        for perovskite in prepared_document.get("perovskites", []):
            perovskite["source"] = absolute_source
        logger.info("Setting perovskite source to input PDF path %s", absolute_source)
        return add_perovskite_structure(prepared_document)

    add_pdf_perovskite_structure._tool_schema = deepcopy(
        add_perovskite_structure._tool_schema
    )
    add_pdf_perovskite_structure._tool_schema["function"]["name"] = (
        "add_perovskite_structure"
    )
    return add_pdf_perovskite_structure


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
    "list_registered_property_names",
    "make_pdf_add_perovskite_tool",
    "search_perovskite_structures",
]
