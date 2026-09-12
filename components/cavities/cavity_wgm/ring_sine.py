import gdsfactory as gf
import numpy as np
import YanglabPDK.YanglabUtils as Utils
import YanglabPDK.YanglabSections as Sections

from YanglabPDK.components.couplers.coupler_ring import coupler_halfring
from YanglabPDK.components.bends.bend_circular import bend_circular
from YanglabPDK.components.waveguides.straight import straight

from functools import partial

@gf.cell
def ring_sine(
    gap: float = 0.2,
    radius: float = 50.0,
    length_x: float = 4.0,
    length_y: float = 0.6,
    width_wg: float = 1,
    width_bend: float = 1,
    period: float = 1,
    delta_width_bend: float = 0.5,
    points: int = 10000,
    buffer: float = 3,
    length_extension_up: float = 500,
    length_extension_down: float = 500
) -> gf.Component:

    if length_y < 0:
        raise ValueError(f"length_y={length_y} must be >= 0")

    if length_x < 0:
        raise ValueError(f"length_x={length_x} must be >= 0")

    c1 = gf.Component()
    c2 = gf.Component()
    theta = np.linspace(0, 2*np.pi, points)
    vertices_in = [(radius-width_bend/2+delta_width_bend*np.sin(2*np.pi*theta/period*radius))*np.cos(theta), 
                   (radius-width_bend/2+delta_width_bend*np.sin(2*np.pi*theta/period*radius))*np.sin(theta)]
    circle_inside = c1.add_polygon(np.array(vertices_in).T, layer=Sections.LAYER.NR)
    
    vertices_out = [(radius+width_bend/2)*np.cos(theta), (radius+width_bend/2)*np.sin(theta)] 
    circle_outside = c2.add_polygon(np.array(vertices_out).T, layer=Sections.LAYER.NR)

    c3 = gf.boolean(c2, c1, operation="not", layer=Sections.LAYER.NR)

    c4 = gf.Component()
    circle_pos = c4 << gf.components.ring(radius=radius, width=width_bend + buffer + width_bend/2, layer=Sections.LAYER.NR)
    
    c5 = gf.boolean(c4, c3, operation="not", layer=Sections.LAYER.NR)
    c5 = Utils.remap_layers(c5, old_layer=Sections.LAYER.NR, new_layer=Sections.LAYER.PR)

    wg1 = c3.add_ref(straight(length=length_extension_up, width=width_wg))
    wg2 = c3.add_ref(straight(length=length_extension_down, width=width_wg))
    wg1.move([-length_extension_up/2, radius+width_bend/2+width_wg/2+gap])
    wg2.move([-length_extension_down/2, -radius-width_bend/2-width_wg/2-gap])

    c3.add_port("o1", port=wg1.ports["o1"])
    c3.add_port("o2", port=wg1.ports["o2"])
    c3.add_port("o3", port=wg2.ports["o1"])
    c3.add_port("o4", port=wg2.ports["o2"])

    c3.add_ref(c5)
    c3 = Utils.pos_neg_seperate(c3)
    
    return c3
    

if __name__ == "__main__":
    c = ring_sine()
    c.plot()
    c.show()