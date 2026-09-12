import gdsfactory as gf

import YanglabPDK.YanglabUtils as Utils
import YanglabPDK.YanglabSections as Sections

from YanglabPDK.components.couplers.coupler_ring import coupler_halfring
from YanglabPDK.components.bends.bend_circular import bend_circular
from YanglabPDK.components.waveguides.straight import straight

from functools import partial

@gf.cell
def dual_ring(
    gap_wg: float = 0.2,
    gap_ring: float = 0.2,
    radius: float = 10.0,
    width_wg: float = 1,
    width_ring: float = 1.2,
    buffer: float = 3,
    length_extension_left: float = 0.0,
    length_extension_right: float = 0.0
) -> gf.Component:
    """Returns two identical coupled ring, one point coupled to waveguide."""

    c = gf.Component()

    wg_half_ring = c << coupler_halfring(
        gap=gap_wg,
        radius=radius,
        length_x=0.0,
        width_wg=width_wg,
        width_bend=width_ring,
        buffer=buffer,
        length_extension_left=length_extension_left,
        length_extension_right=length_extension_right
    )

    quarter_ring_right = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)
    quarter_ring_left = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)

    quarter_ring_left.connect(port="o2", other=wg_half_ring.ports["o2"])
    quarter_ring_right.connect(port="o1", other=wg_half_ring.ports["o3"])

    coupled_ring_right_bottom = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)
    coupled_ring_right_bottom.movey(radius*2 + gap_ring + width_ring + width_wg + gap_wg)
    coupled_ring_right_top = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)
    coupled_ring_right_top.connect(port="o1", other=coupled_ring_right_bottom.ports["o2"])
    coupled_ring_left_top = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)
    coupled_ring_left_top.connect(port="o1", other=coupled_ring_right_top.ports["o2"])
    coupled_ring_left_bottom = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)
    coupled_ring_left_bottom.connect(port="o1", other=coupled_ring_left_top.ports["o2"])

    c.add_port("o2", port=wg_half_ring.ports["o4"])
    c.add_port("o1", port=wg_half_ring.ports["o1"])
    return Utils.pos_neg_seperate(c)

if __name__ == "__main__":
    c = dual_ring(radius=50)
    c.plot()
    c.show()