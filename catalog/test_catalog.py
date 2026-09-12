"""Regression tests for the static YanglabPDK component catalog."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from generate_manifest import PACKAGE_ROOT, discover, main


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.components = discover(PACKAGE_ROOT)

    def test_discovers_expected_cells(self):
        ids = {item["id"] for item in self.components if item["status"] != "error"}
        self.assertIn("components.waveguides.straight:straight", ids)
        self.assertIn("components.cavities.cavity_wgm.ring_single:ring_single", ids)
        self.assertIn("components.mzis.mzi_mmi:mzi_mmi", ids)

    def test_ids_and_thumbnail_names_are_unique(self):
        cells = [item for item in self.components if item["status"] != "error"]
        self.assertEqual(len({item["id"] for item in cells}), len(cells))
        self.assertEqual(len({item["thumbnail"] for item in cells}), len(cells))

    def test_every_cell_has_insertable_parameter_metadata(self):
        for component in self.components:
            if component["status"] == "error":
                continue
            with self.subTest(component=component["id"]):
                self.assertTrue(component["module"].startswith("YanglabPDK.components."))
                for parameter in component["parameters"]:
                    self.assertIn(parameter["kind"], {"required", "literal", "expression"})
                    self.assertTrue(parameter["name"].isidentifier())


if __name__ == "__main__":
    unittest.main(verbosity=2)
