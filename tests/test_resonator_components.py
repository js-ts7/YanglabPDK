"""Smoke tests for the added resonator cells."""

import unittest

import gdsfactory as gf

from YanglabPDK import LAYER
from YanglabPDK.components.cavities.cavity_wgm import (
    EO_racetrack,
    dual_ring,
    dual_ring_drop_heater,
    ring_PhC,
    ring_sine,
)


class ResonatorComponentTests(unittest.TestCase):
    def setUp(self):
        gf.clear_cache()

    def assert_resist_layers(self, component):
        layers = {tuple(layer) for layer in component.layers}
        self.assertIn(tuple(LAYER.PR), layers)
        self.assertIn(tuple(LAYER.NR), layers)

    def test_dual_ring(self):
        component = dual_ring()
        self.assertEqual({port.name for port in component.ports}, {"o1", "o2"})
        self.assert_resist_layers(component)

    def test_dual_ring_drop_heater(self):
        component = dual_ring_drop_heater()
        self.assertTrue({"o1", "o2", "o3", "o4"}.issubset({port.name for port in component.ports}))
        self.assert_resist_layers(component)

    def test_eo_racetrack(self):
        component = EO_racetrack(length_y=100)
        self.assertEqual({port.name for port in component.ports}, {"o1", "o2"})
        self.assert_resist_layers(component)

    def test_ring_sine(self):
        component = ring_sine()
        self.assertEqual({port.name for port in component.ports}, {"o1", "o2", "o3", "o4"})
        self.assert_resist_layers(component)

    def test_ring_phc_is_exported(self):
        self.assertTrue(callable(ring_PhC))


if __name__ == "__main__":
    unittest.main(verbosity=2)
