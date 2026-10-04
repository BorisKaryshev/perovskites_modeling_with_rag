"""Small PostgreSQL repository. SQL rows never leak into the public API."""
from __future__ import annotations

from decimal import Decimal

import psycopg

from .models import (
    Additive, Compound, Ion, Layer, LayerStack, Perovskite, PerovskiteData,
    Property, Structure,
)


class DBA:
    """Store and search validated Pydantic models in normalized tables."""

    _perovskite_search = {
        "id": "p.model_id::text ~* %s",
        "formula": "p.formula::text ~* %s",
        "source": "p.source::text ~* %s",
        "notes": "p.notes::text ~* %s",
        "structure.family": "EXISTS (SELECT 1 FROM perovskite.structure s WHERE s.perovskite_id = p.id AND s.family::text ~* %s)",
        "structure.space_group": "EXISTS (SELECT 1 FROM perovskite.structure s WHERE s.perovskite_id = p.id AND s.space_group::text ~* %s)",
        "structure.dimensionality": "EXISTS (SELECT 1 FROM perovskite.structure s WHERE s.perovskite_id = p.id AND s.dimensionality::text ~* %s)",
        "structure.cif": "EXISTS (SELECT 1 FROM perovskite.structure s WHERE s.perovskite_id = p.id AND s.cif::text ~* %s)",
        "ions.site": "EXISTS (SELECT 1 FROM perovskite.ion i WHERE i.perovskite_id = p.id AND i.site::text ~* %s)",
        "ions.coefficient": "EXISTS (SELECT 1 FROM perovskite.ion i WHERE i.perovskite_id = p.id AND i.coefficient::text ~* %s)",
        "ions.compound.name": "EXISTS (SELECT 1 FROM perovskite.ion i JOIN perovskite.compound c ON c.id = i.compound_id WHERE i.perovskite_id = p.id AND c.name::text ~* %s)",
        "ions.compound.formula": "EXISTS (SELECT 1 FROM perovskite.ion i JOIN perovskite.compound c ON c.id = i.compound_id WHERE i.perovskite_id = p.id AND c.formula::text ~* %s)",
        "ions.compound.smiles": "EXISTS (SELECT 1 FROM perovskite.ion i JOIN perovskite.compound c ON c.id = i.compound_id WHERE i.perovskite_id = p.id AND c.smiles::text ~* %s)",
        "ions.compound.iupac_name": "EXISTS (SELECT 1 FROM perovskite.ion i JOIN perovskite.compound c ON c.id = i.compound_id WHERE i.perovskite_id = p.id AND c.iupac_name::text ~* %s)",
        "ions.compound.cas_number": "EXISTS (SELECT 1 FROM perovskite.ion i JOIN perovskite.compound c ON c.id = i.compound_id WHERE i.perovskite_id = p.id AND c.cas_number::text ~* %s)",
        "ions.compound.source_compound": "EXISTS (SELECT 1 FROM perovskite.ion i JOIN perovskite.compound c ON c.id = i.compound_id WHERE i.perovskite_id = p.id AND c.source_compound::text ~* %s)",
        "additives.compound.name": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND c.name::text ~* %s)",
        "additives.compound.formula": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND c.formula::text ~* %s)",
        "additives.compound.smiles": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND c.smiles::text ~* %s)",
        "additives.compound.iupac_name": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND c.iupac_name::text ~* %s)",
        "additives.compound.cas_number": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND c.cas_number::text ~* %s)",
        "additives.compound.source_compound": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND c.source_compound::text ~* %s)",
        "additives.amount": "EXISTS (SELECT 1 FROM perovskite.additive a WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND a.amount::text ~* %s)",
        "additives.unit": "EXISTS (SELECT 1 FROM perovskite.additive a WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND a.unit::text ~* %s)",
        "additives.basis": "EXISTS (SELECT 1 FROM perovskite.additive a WHERE a.perovskite_id = p.id AND a.kind = 'additive' AND a.basis::text ~* %s)",
        "impurities.compound.name": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND c.name::text ~* %s)",
        "impurities.compound.formula": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND c.formula::text ~* %s)",
        "impurities.compound.smiles": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND c.smiles::text ~* %s)",
        "impurities.compound.iupac_name": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND c.iupac_name::text ~* %s)",
        "impurities.compound.cas_number": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND c.cas_number::text ~* %s)",
        "impurities.compound.source_compound": "EXISTS (SELECT 1 FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND c.source_compound::text ~* %s)",
        "impurities.amount": "EXISTS (SELECT 1 FROM perovskite.additive a WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND a.amount::text ~* %s)",
        "impurities.unit": "EXISTS (SELECT 1 FROM perovskite.additive a WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND a.unit::text ~* %s)",
        "impurities.basis": "EXISTS (SELECT 1 FROM perovskite.additive a WHERE a.perovskite_id = p.id AND a.kind = 'impurity' AND a.basis::text ~* %s)",
        "properties.name": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.perovskite_id = p.id AND pr.name::text ~* %s)",
        "properties.value": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.perovskite_id = p.id AND pr.value::text ~* %s)",
        "properties.unit": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.perovskite_id = p.id AND pr.unit::text ~* %s)",
        "properties.method": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.perovskite_id = p.id AND pr.method::text ~* %s)",
        "properties.conditions": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.perovskite_id = p.id AND pr.conditions::text ~* %s)",
        "properties.source": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.perovskite_id = p.id AND pr.source::text ~* %s)",
    }

    _stack_search = {
        "architecture": "ls.architecture::text ~* %s",
        "layers.material": "EXISTS (SELECT 1 FROM perovskite.layer l WHERE l.layer_stack_id = ls.id AND l.material::text ~* %s)",
        "layers.perovskite_id": "EXISTS (SELECT 1 FROM perovskite.layer l JOIN perovskite.perovskite p ON p.id = l.perovskite_id WHERE l.layer_stack_id = ls.id AND p.model_id::text ~* %s)",
        "layers.thickness_nm": "EXISTS (SELECT 1 FROM perovskite.layer l WHERE l.layer_stack_id = ls.id AND l.thickness_nm::text ~* %s)",
        "properties.name": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.layer_stack_id = ls.id AND pr.name::text ~* %s)",
        "properties.value": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.layer_stack_id = ls.id AND pr.value::text ~* %s)",
        "properties.unit": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.layer_stack_id = ls.id AND pr.unit::text ~* %s)",
        "properties.method": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.layer_stack_id = ls.id AND pr.method::text ~* %s)",
        "properties.conditions": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.layer_stack_id = ls.id AND pr.conditions::text ~* %s)",
        "properties.source": "EXISTS (SELECT 1 FROM perovskite.property pr WHERE pr.layer_stack_id = ls.id AND pr.source::text ~* %s)",
    }

    def __init__(self, dsn: str):
        self.dsn = dsn

    def save(self, value: PerovskiteData) -> int:
        value = PerovskiteData.model_validate(value)
        with psycopg.connect(self.dsn) as connection:
            dataset_id = connection.execute(
                "INSERT INTO perovskite.dataset DEFAULT VALUES RETURNING id"
            ).fetchone()[0]
            self._write(connection, dataset_id, value)
        return dataset_id

    def get(self, dataset_id: int) -> PerovskiteData | None:
        with psycopg.connect(self.dsn) as connection:
            if connection.execute(
                "SELECT 1 FROM perovskite.dataset WHERE id = %s", (dataset_id,)
            ).fetchone() is None:
                return None
            return self._load_dataset(connection, dataset_id)

    def all(self) -> list[PerovskiteData]:
        with psycopg.connect(self.dsn) as connection:
            ids = connection.execute("SELECT id FROM perovskite.dataset ORDER BY id").fetchall()
            return [self._load_dataset(connection, row[0]) for row in ids]

    def replace(self, dataset_id: int, value: PerovskiteData) -> bool:
        value = PerovskiteData.model_validate(value)
        with psycopg.connect(self.dsn) as connection:
            if connection.execute(
                "SELECT 1 FROM perovskite.dataset WHERE id = %s FOR UPDATE", (dataset_id,)
            ).fetchone() is None:
                return False
            connection.execute("DELETE FROM perovskite.layer_stack WHERE dataset_id = %s", (dataset_id,))
            connection.execute("DELETE FROM perovskite.perovskite WHERE dataset_id = %s", (dataset_id,))
            connection.execute("DELETE FROM perovskite.compound WHERE dataset_id = %s", (dataset_id,))
            connection.execute(
                "UPDATE perovskite.dataset SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (dataset_id,),
            )
            self._write(connection, dataset_id, value)
        return True

    def delete(self, dataset_id: int) -> bool:
        with psycopg.connect(self.dsn) as connection:
            cursor = connection.execute(
                "DELETE FROM perovskite.dataset WHERE id = %s", (dataset_id,)
            )
        return cursor.rowcount == 1

    def search(self, **patterns: str) -> list[Perovskite]:
        """Find materials. Values are case-insensitive PostgreSQL regexes."""
        with psycopg.connect(self.dsn) as connection:
            ids = self._search_ids(
                connection, "perovskite.perovskite p", "p.id",
                self._perovskite_search, patterns,
            )
            return [self._load_perovskite(connection, row[0]) for row in ids]

    def search_layer_stacks(self, **patterns: str) -> list[LayerStack]:
        """Find layer stacks. Values use the same regex syntax as search()."""
        with psycopg.connect(self.dsn) as connection:
            ids = self._search_ids(
                connection, "perovskite.layer_stack ls", "ls.id",
                self._stack_search, patterns,
            )
            return [self._load_stack(connection, row[0]) for row in ids]

    @staticmethod
    def _search_ids(connection, root: str, id_column: str,
                    allowed: dict[str, str], patterns: dict[str, str]):
        unknown = patterns.keys() - allowed.keys()
        if unknown:
            raise ValueError(f"Unknown search fields: {', '.join(sorted(unknown))}")
        clauses = [allowed[field] for field in patterns]
        where = " AND ".join(clauses) if clauses else "true"
        return connection.execute(
            f"SELECT {id_column} FROM {root} WHERE {where} ORDER BY {id_column}",
            list(patterns.values()),
        ).fetchall()

    def _write(self, connection, dataset_id: int, data: PerovskiteData) -> None:
        material_ids = {}
        for position, material in enumerate(data.perovskites):
            material_id = connection.execute(
                """INSERT INTO perovskite.perovskite
                   (dataset_id, position, model_id, formula, source, notes)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (dataset_id, position, material.id, material.formula,
                 material.source, material.notes),
            ).fetchone()[0]
            material_ids[material.id] = material_id
            if material.structure is not None:
                s = material.structure
                connection.execute(
                    """INSERT INTO perovskite.structure
                       (perovskite_id, family, space_group, dimensionality, cif)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (material_id, s.family, s.space_group, s.dimensionality, s.cif),
                )
            for item_position, ion in enumerate(material.ions):
                compound_id = self._insert_compound(connection, dataset_id, ion.compound)
                connection.execute(
                    """INSERT INTO perovskite.ion
                       (perovskite_id, position, site, compound_id, coefficient)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (material_id, item_position, ion.site, compound_id, ion.coefficient),
                )
            for kind, items in (("additive", material.additives), ("impurity", material.impurities)):
                for item_position, item in enumerate(items):
                    compound_id = self._insert_compound(connection, dataset_id, item.compound)
                    connection.execute(
                        """INSERT INTO perovskite.additive
                           (perovskite_id, position, kind, compound_id, amount, unit, basis)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (material_id, item_position, kind, compound_id,
                         item.amount, item.unit, item.basis),
                    )
            for item_position, item in enumerate(material.properties):
                self._insert_property(connection, dataset_id, item_position, item,
                                      perovskite_id=material_id)

        for position, stack in enumerate(data.layer_stacks):
            stack_id = connection.execute(
                """INSERT INTO perovskite.layer_stack (dataset_id, position, architecture)
                   VALUES (%s, %s, %s) RETURNING id""",
                (dataset_id, position, stack.architecture),
            ).fetchone()[0]
            for item_position, layer in enumerate(stack.layers):
                connection.execute(
                    """INSERT INTO perovskite.layer
                       (dataset_id, layer_stack_id, position, material, perovskite_id, thickness_nm)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (dataset_id, stack_id, item_position, layer.material,
                     material_ids.get(layer.perovskite_id), layer.thickness_nm),
                )
            for item_position, item in enumerate(stack.properties):
                self._insert_property(connection, dataset_id, item_position, item,
                                      layer_stack_id=stack_id)

    @staticmethod
    def _insert_compound(connection, dataset_id: int, item: Compound) -> int:
        return connection.execute(
            """INSERT INTO perovskite.compound
               (dataset_id, name, formula, smiles, iupac_name, cas_number, source_compound)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (dataset_id, item.name, item.formula, item.smiles, item.iupac_name,
             item.cas_number, item.source_compound),
        ).fetchone()[0]

    @staticmethod
    def _insert_property(connection, dataset_id: int, position: int, item: Property,
                         perovskite_id=None, layer_stack_id=None) -> None:
        connection.execute(
            """INSERT INTO perovskite.property
               (dataset_id, perovskite_id, layer_stack_id, position, name, value,
                unit, method, conditions, source)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (dataset_id, perovskite_id, layer_stack_id, position, item.name,
             item.value, item.unit, item.method, item.conditions, item.source),
        )

    def _load_dataset(self, connection, dataset_id: int) -> PerovskiteData:
        material_ids = connection.execute(
            "SELECT id FROM perovskite.perovskite WHERE dataset_id = %s ORDER BY position",
            (dataset_id,),
        ).fetchall()
        stack_ids = connection.execute(
            "SELECT id FROM perovskite.layer_stack WHERE dataset_id = %s ORDER BY position",
            (dataset_id,),
        ).fetchall()
        return PerovskiteData(
            perovskites=[self._load_perovskite(connection, row[0]) for row in material_ids],
            layer_stacks=[self._load_stack(connection, row[0]) for row in stack_ids],
        )

    def _load_perovskite(self, connection, material_id: int) -> Perovskite:
        row = connection.execute(
            "SELECT model_id, formula, source, notes FROM perovskite.perovskite WHERE id = %s",
            (material_id,),
        ).fetchone()
        structure_row = connection.execute(
            "SELECT family, space_group, dimensionality, cif FROM perovskite.structure WHERE perovskite_id = %s",
            (material_id,),
        ).fetchone()
        ions = connection.execute(
            """SELECT i.site, i.coefficient, c.name, c.formula, c.smiles,
                      c.iupac_name, c.cas_number, c.source_compound
               FROM perovskite.ion i JOIN perovskite.compound c ON c.id = i.compound_id
               WHERE i.perovskite_id = %s ORDER BY i.position""",
            (material_id,),
        ).fetchall()
        return Perovskite(
            id=row[0], formula=row[1], source=row[2], notes=row[3],
            structure=None if structure_row is None else Structure(
                family=structure_row[0], space_group=structure_row[1],
                dimensionality=structure_row[2], cif=structure_row[3]),
            ions=[Ion(site=item[0], coefficient=float(item[1]),
                      compound=self._compound(item[2:])) for item in ions],
            additives=self._load_additives(connection, material_id, "additive"),
            impurities=self._load_additives(connection, material_id, "impurity"),
            properties=self._load_properties(connection, "perovskite_id", material_id),
        )

    def _load_stack(self, connection, stack_id: int) -> LayerStack:
        architecture = connection.execute(
            "SELECT architecture FROM perovskite.layer_stack WHERE id = %s", (stack_id,)
        ).fetchone()[0]
        layers = connection.execute(
            """SELECT l.material, p.model_id, l.thickness_nm
               FROM perovskite.layer l
               LEFT JOIN perovskite.perovskite p ON p.id = l.perovskite_id
               WHERE l.layer_stack_id = %s ORDER BY l.position""",
            (stack_id,),
        ).fetchall()
        return LayerStack(
            architecture=architecture,
            layers=[Layer(material=row[0], perovskite_id=row[1],
                          thickness_nm=self._number(row[2])) for row in layers],
            properties=self._load_properties(connection, "layer_stack_id", stack_id),
        )

    def _load_additives(self, connection, material_id: int, kind: str) -> list[Additive]:
        rows = connection.execute(
            """SELECT a.amount, a.unit, a.basis, c.name, c.formula, c.smiles,
                      c.iupac_name, c.cas_number, c.source_compound
               FROM perovskite.additive a JOIN perovskite.compound c ON c.id = a.compound_id
               WHERE a.perovskite_id = %s AND a.kind = %s ORDER BY a.position""",
            (material_id, kind),
        ).fetchall()
        return [Additive(amount=self._number(row[0]), unit=row[1], basis=row[2],
                         compound=self._compound(row[3:])) for row in rows]

    def _load_properties(self, connection, owner: str, owner_id: int) -> list[Property]:
        rows = connection.execute(
            f"""SELECT name, value, unit, method, conditions, source
                FROM perovskite.property WHERE {owner} = %s ORDER BY position""",
            (owner_id,),
        ).fetchall()
        return [Property(name=row[0], value=float(row[1]), unit=row[2], method=row[3],
                         conditions=row[4], source=row[5]) for row in rows]

    @staticmethod
    def _compound(row) -> Compound:
        return Compound(name=row[0], formula=row[1], smiles=row[2], iupac_name=row[3],
                        cas_number=row[4], source_compound=row[5])

    @staticmethod
    def _number(value: Decimal | None) -> float | None:
        return None if value is None else float(value)
