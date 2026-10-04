import json
import unittest
from unittest.mock import patch

from src.tools.perovskite_database import (
    MODEL_VERSION,
    PEROVSKITE_SEARCH_FIELDS,
    _parse_filters,
    add_perovskite_structure,
    delete_perovskite_structure,
    get_perovskite_model_schema,
    search_perovskite_structures,
)


class FakeDBA:
    def __init__(self, _dsn):
        pass

    def save(self, value):
        self.saved = value
        return 42

    def get(self, dataset_id):
        raise AssertionError(f"get must not be called without confirmation: {dataset_id}")


class PerovskiteDatabaseToolTests(unittest.TestCase):
    def test_model_is_v21_and_schema_has_current_root_fields(self):
        schema = get_perovskite_model_schema()
        self.assertEqual(MODEL_VERSION, "2.1")
        self.assertEqual(
            set(schema["properties"]), {"perovskites", "layer_stacks"}
        )

    def test_add_validates_and_returns_dataset_id(self):
        document = {
            "perovskites": [
                {
                    "id": "test-cspbi3",
                    "formula": "CsPbI3",
                    "ions": [
                        {
                            "site": "A",
                            "compound": {"name": "caesium", "formula": "Cs+"},
                            "coefficient": 1,
                        },
                        {
                            "site": "B",
                            "compound": {"name": "lead", "formula": "Pb2+"},
                            "coefficient": 1,
                        },
                        {
                            "site": "X",
                            "compound": {"name": "iodide", "formula": "I-"},
                            "coefficient": 3,
                        },
                    ],
                }
            ],
            "layer_stacks": [],
        }
        with patch("src.tools.perovskite_database._dsn", return_value="test"), patch(
            "src.tools.perovskite_database.DBA", FakeDBA
        ):
            result = json.loads(add_perovskite_structure(document))
        self.assertTrue(result["ok"])
        self.assertEqual(result["dataset_id"], 42)
        self.assertEqual(result["perovskites"], 1)

    def test_add_rejects_device_property_on_material(self):
        document = {
            "perovskites": [
                {
                    "id": "bad",
                    "formula": "CsPbI3",
                    "ions": [
                        {
                            "site": "A",
                            "compound": {"name": "caesium"},
                            "coefficient": 1,
                        }
                    ],
                    "properties": [{"name": "pce", "value": 20, "unit": "%"}],
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "Photovoltaic metrics"):
            add_perovskite_structure(document)

    def test_add_tool_accepts_native_document_object(self):
        parameters = add_perovskite_structure._tool_schema["function"]["parameters"]
        self.assertEqual(parameters["required"], ["document"])
        self.assertEqual(parameters["properties"]["document"]["type"], "object")
        self.assertNotIn("document_json", parameters["properties"])
        self.assertIn("Perovskite", parameters["$defs"])
        self.assertNotIn("$defs", parameters["properties"]["document"])
        self.assertEqual(
            parameters["properties"]["document"]["properties"]["perovskites"]
            ["items"]["$ref"],
            "#/$defs/Perovskite",
        )

    def test_add_validation_error_explains_required_ion_shape(self):
        with self.assertRaisesRegex(ValueError, "ions.*array"):
            add_perovskite_structure({
                "perovskites": [{
                    "id": "bad", "formula": "CsPbI3", "ions": "CsPbI3"
                }],
                "layer_stacks": [],
            })

    def test_filter_parser_accepts_fields_and_rejects_unknown_ones(self):
        self.assertEqual(
            _parse_filters('{"formula":"^Cs","properties.name":"band_gap"}',
                           PEROVSKITE_SEARCH_FIELDS),
            {"formula": "^Cs", "properties.name": "band_gap"},
        )
        with self.assertRaisesRegex(ValueError, "Unknown search fields"):
            _parse_filters('{"not_a_field":"x"}', PEROVSKITE_SEARCH_FIELDS)

    def test_search_rejects_unknown_entity_before_database_access(self):
        with self.assertRaisesRegex(ValueError, "entity must be"):
            search_perovskite_structures("device", "{}")

    def test_delete_requires_exact_confirmation_before_database_access(self):
        result = json.loads(delete_perovskite_structure(7, "yes"))
        self.assertFalse(result["deleted"])
        self.assertIn("DELETE DATASET 7", result["error"])


if __name__ == "__main__":
    unittest.main()
