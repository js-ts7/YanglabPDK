"""Curated metadata layered over automatic component discovery.

Keys use ``relative.module:function`` so similarly named cells remain distinct.
Only user-facing cells need an entry here. Other ``@gf.cell`` functions are still
discovered and appear in the extension under "Discovered".
"""

COMPONENT_OVERRIDES = {
    "components.waveguides.straight:straight": {
        "title": "Straight waveguide",
        "description": "Straight optical waveguide with positive/negative resist geometry.",
        "recommended": ["length", "width", "buffer"],
    },
    "components.waveguides.straight_heater_metal:straight_heater_metal_undercut": {
        "title": "Metal heater waveguide",
        "description": "Straight waveguide with metal heater and undercut geometry.",
    },
    "components.bends.bend_euler:bend_euler": {
        "title": "Euler bend",
        "description": "Low-loss Euler bend.",
        "recommended": ["radius", "angle", "width", "buffer"],
    },
    "components.bends.bend_circular:bend_circular": {
        "title": "Circular bend",
        "description": "Constant-radius circular bend.",
        "recommended": ["radius", "angle", "width", "buffer"],
    },
    "components.bends.bend_s:bend_s": {
        "title": "S bend",
        "description": "S-shaped waveguide transition.",
    },
    "components.bends.bend_bezier:bend_bezier": {
        "title": "Bezier bend",
        "description": "Bezier-profile waveguide bend.",
    },
    "components.couplers.coupler:coupler": {
        "title": "Directional coupler",
        "description": "Symmetric directional coupler.",
    },
    "components.couplers.coupler:coupler_straight": {
        "title": "Straight coupling section",
        "description": "Parallel straight coupling region.",
    },
    "components.couplers.coupler_ring:coupler_halfring": {
        "title": "Half-ring coupler",
        "description": "Bus-to-half-ring coupling section.",
    },
    "components.couplers.coupler_ring:coupler_halfring_pulley": {
        "title": "Pulley half-ring coupler",
        "description": "Extended pulley coupling section for a ring resonator.",
    },
    "components.couplers.coupler_adiabatic:coupler_adiabatic_full": {
        "title": "Adiabatic coupler",
        "description": "Full adiabatic directional coupler.",
    },
    "components.cavities.cavity_wgm.ring_single:ring_single": {
        "title": "Single ring resonator",
        "description": "Single-bus whispering-gallery ring resonator.",
        "recommended": ["radius", "gap", "width", "wg_width", "buffer"],
    },
    "components.cavities.cavity_wgm.ring_pulley:ring_single_pulley": {
        "title": "Pulley ring resonator",
        "description": "Ring resonator with an extended pulley bus coupler.",
    },
    "components.cavities.cavity_wgm.dual_ring:dual_ring": {
        "title": "Dual ring resonator",
        "description": "Coupled dual-ring resonator.",
    },
    "components.cavities.cavity_wgm.dual_ring_drop_heater:dual_ring_drop_heater": {
        "title": "Heated dual-ring add-drop",
        "description": "Dual-ring add-drop structure with integrated heaters.",
    },
    "components.cavities.cavity_wgm.EO_racetrack:EO_racetrack": {
        "title": "Electro-optic racetrack",
        "description": "Racetrack resonator with electro-optic electrodes.",
        "previewParameters": {"length_y": 100.0},
    },
    "components.cavities.cavity_wgm.ring_PhC:ring_PhC": {
        "title": "Photonic-crystal ring",
        "description": "Ring resonator carrying a photonic-crystal modulation.",
    },
    "components.cavities.cavity_wgm.ring_sine:ring_sine": {
        "title": "Sinusoidal ring",
        "description": "Ring resonator with sinusoidally modulated boundary geometry.",
    },
    "components.filters.dbr:dbr": {
        "title": "Distributed Bragg reflector",
        "description": "Periodic-width DBR filter.",
        "recommended": ["n"],
    },
    "components.filters.awg:awg": {
        "title": "Arrayed waveguide grating",
        "description": "Arrayed waveguide grating layout.",
    },
    "components.mmis.mmi1x2:mmi1x2": {
        "title": "MMI 1x2",
        "description": "One-input, two-output multimode interferometer.",
    },
    "components.mmis.mmi2x2:mmi2x2": {
        "title": "MMI 2x2",
        "description": "Two-input, two-output multimode interferometer.",
    },
    "components.mzis.mzi_mmi:mzi_mmi": {
        "title": "MMI Mach-Zehnder interferometer",
        "description": "Mach-Zehnder interferometer assembled from MMI splitters.",
    },
    "components.reflectors.sagnac_loop:sagnac_loop": {
        "title": "Sagnac loop",
        "description": "Loop mirror based on a directional coupler.",
    },
    "components.lasers.sagnet_feedback:sagnet_feedback": {
        "title": "Sagnac feedback circuit",
        "description": "Photonic feedback circuit using a Sagnac loop.",
    },
    "components.spirals.spiral_double:spiral_double": {
        "title": "Double spiral",
        "description": "Compact long-path double spiral waveguide.",
        "previewParameters": {"min_bend_radius": 10.0},
    },
    "components.tapers.taper:taper": {
        "title": "Waveguide taper",
        "description": "Linear waveguide-width transition.",
    },
    "components.tapers.taper:taper_buffer": {
        "title": "Buffered taper",
        "description": "Waveguide taper with process buffer geometry.",
    },
    "components.utils.mark:cross": {
        "title": "Cross alignment mark",
        "description": "Cross-shaped lithography alignment mark.",
    },
}
