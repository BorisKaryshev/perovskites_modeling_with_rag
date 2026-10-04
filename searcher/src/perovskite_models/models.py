"""Simplified model v2.1: material cards and ordered layer stacks.

One selected composition per card. Alternatives are separate cards.
Coefficients count ions per formula unit, not occupancy percentages.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Compound(_Model):
    """Identity of an ion, additive, or impurity."""

    name: str = Field(min_length=1)
    formula: str | None = None
    smiles: str | None = None
    iupac_name: str | None = None
    cas_number: str | None = None
    source_compound: str | None = None


class Ion(_Model):
    """Component and its coefficient, e.g. X: iodine, coefficient=3."""

    site: Literal["A", "B", "X", "spacer", "other"]
    compound: Compound
    coefficient: float = Field(gt=0)


class Additive(_Model):
    """Introduced additive or impurity; no lattice incorporation is implied."""

    compound: Compound
    amount: float | None = Field(default=None, ge=0)
    unit: str | None = None
    basis: str | None = None

    @model_validator(mode="after")
    def check_amount(self):
        if self.amount is not None and (not self.unit or not self.basis):
            raise ValueError("Known amount requires a unit and a basis (solution, dry film, etc.)")
        return self


class Structure(_Model):
    """Optional description; composition alone does not establish this class."""

    family: str | None = None
    space_group: str | None = None
    dimensionality: int | None = Field(default=None, ge=0, le=3)
    cif: str | None = None


class Property(_Model):
    """A scalar measurement or calculation, with its context."""

    name: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    method: str | None = None
    conditions: str | None = None
    source: str | None = None


class Layer(_Model):
    """A physical layer; list position determines its order in a stack."""

    material: str = Field(min_length=1)
    perovskite_id: str | None = Field(default=None, min_length=1)
    thickness_nm: float | None = Field(default=None, gt=0)


class LayerStack(_Model):
    """Ordered layers; performance measurements concern the complete stack."""

    architecture: str | None = None
    layers: list[Layer] = Field(min_length=1)
    properties: list[Property] = Field(default_factory=list)


class Perovskite(_Model):
    """Search result card: composition, optional structure, and observations."""

    id: str = Field(min_length=1)
    formula: str = Field(min_length=1)
    ions: list[Ion] = Field(min_length=1)
    structure: Structure | None = None
    additives: list[Additive] = Field(default_factory=list)
    impurities: list[Additive] = Field(default_factory=list)
    properties: list[Property] = Field(default_factory=list)
    source: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def check_property_scope(self):
        # These exact canonical names denote photovoltaic device metrics.
        device_metrics = {"pce", "voc", "jsc", "fill_factor", "eqe"}
        if any(p.name.casefold() in device_metrics for p in self.properties):
            raise ValueError("Photovoltaic metrics belong in layer_stacks[].properties")
        return self


class PerovskiteData(_Model):
    """JSON envelope; IDs are unique within this document."""

    perovskites: list[Perovskite] = Field(default_factory=list)
    layer_stacks: list[LayerStack] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_references(self):
        ids = [p.id for p in self.perovskites]
        if len(ids) != len(set(ids)):
            raise ValueError("Perovskite IDs must be unique within the document")
        known = set(ids)
        for stack in self.layer_stacks:
            for layer in stack.layers:
                if layer.perovskite_id is not None and layer.perovskite_id not in known:
                    raise ValueError(f"Unknown perovskite_id: {layer.perovskite_id}")
        return self


__all__ = ["Compound", "Ion", "Additive", "Structure", "Property", "Layer",
           "LayerStack", "Perovskite", "PerovskiteData"]
