import gdsfactory as gf

import YanglabPDK.YanglabLayerStack as LayerStack
import YanglabPDK.YanglabUtils as Utils
import YanglabPDK.YanglabSections as Sections

from YanglabPDK.components.couplers.coupler_ring import coupler_halfring
from YanglabPDK.components.bends.bend_circular import bend_circular
from YanglabPDK.components.waveguides.straight import straight

from functools import partial

@gf.cell
def EO_racetrack(
    wg_gap: float = 0.2,
    radius: float = 10.0,
    length_x: float = 500.0,
    length_y: float = 0.0,
    width_wg: float = 1,
    width_bend: float = 1,
    buffer: float = 3,
    length_extension_left: float = 500,
    length_extension_right: float = 500,
    electrode_gap: float = 8.0, # distance between two electrodes
    electrode_width: float = 30.0, # width of each electrode
    pad_length: float = 100.0, # length of electrode pad,
    electrode_length_difference: float = 0.0, # length difference between electrodes and waveguide straight on one side, avoid bend modulation
) -> gf.Component:

    if length_y < 0:
        raise ValueError(f"length_y={length_y} must be >= 0")

    if length_x < 0:
        raise ValueError(f"length_x={length_x} must be >= 0")

    c = gf.Component()

    cb = c << coupler_halfring(
        gap=wg_gap,
        radius=radius,
        length_x=length_x,
        width_wg=width_wg,
        width_bend=width_bend,
        buffer=buffer,
        length_extension_left=length_extension_left,
        length_extension_right=length_extension_right
    )

    sl = c << straight(length=length_y, width=width_bend, buffer=buffer)
    sr = c << straight(length=length_y, width=width_bend, buffer=buffer)
    st = c << straight(length=length_x, width=width_bend, buffer=buffer)
    bl = c << bend_circular(radius=radius, width=width_bend, buffer=buffer)
    br = c << bend_circular(radius=radius, width=width_bend, buffer=buffer)

    sl.connect(port="o1", other=cb.ports["o2"])
    bl.connect(port="o2", other=sl.ports["o2"])
    st.connect(port="o2", other=bl.ports["o1"])
    br.connect(port="o2", other=st.ports["o1"])
    sr.connect(port="o1", other=br.ports["o1"])
    sr.connect(port="o2", other=cb.ports["o3"])

    c.add_port("o2", port=cb.ports["o4"])
    c.add_port("o1", port=cb.ports["o1"])

    electrode_right = gf.Component()
    electrode_straight = gf.components.rectangle(
        size=(electrode_width, length_y - electrode_length_difference*2),
        layer=LayerStack.YanglabLayerMap.MT1,
    )
    electrode_right_straight1 = electrode_right << electrode_straight
    electrode_right_straight1.move((radius + electrode_gap / 2, width_wg/2 + wg_gap + width_bend/2 + radius + electrode_length_difference))
    electrode_right_pad1 = electrode_right << gf.components.rectangle(
        size=(pad_length, pad_length),
        layer=LayerStack.YanglabLayerMap.MT1,
    )
    electrode_right_pad1.move((radius + electrode_gap / 2 + electrode_width, width_wg/2 + wg_gap + width_bend/2 + radius + length_y/2))
    electrode_right_straight2 = electrode_right << electrode_straight
    electrode_right_straight2.move((radius + electrode_gap / 2, width_wg/2 + wg_gap + width_bend/2 + radius + electrode_length_difference))
    electrode_right_straight2.mirror_x(radius)

    electrode_left = gf.Component()
    electrode_left_straight = gf.components.rectangle(
        size=(electrode_width, length_y - electrode_length_difference*2),
        layer=LayerStack.YanglabLayerMap.MT1,
    )
    electrode_left_straight1 = electrode_left << electrode_left_straight
    electrode_left_straight1.move((-radius - electrode_gap / 2 - electrode_width, width_wg/2 + wg_gap + width_bend/2 + radius + electrode_length_difference))
    electrode_left_pad1 = electrode_left << gf.components.rectangle(
        size=(pad_length, pad_length),
        layer=LayerStack.YanglabLayerMap.MT1,
    )   
    electrode_left_pad1.move((-radius - electrode_gap / 2 - electrode_width - pad_length, width_wg/2 + wg_gap + width_bend/2 + radius + length_y/2))
    electrode_left_straight2 = electrode_left << electrode_left_straight    
    electrode_left_straight2.move((-radius - electrode_gap / 2 - electrode_width, width_wg/2 + wg_gap + width_bend/2 + radius + electrode_length_difference))
    electrode_left_straight2.mirror_x(-radius)

    electrode_connector = gf.components.rectangle(
        size=(2*radius - width_bend - electrode_gap, pad_length),
        layer=LayerStack.YanglabLayerMap.MT1,
    )
    electrode_connector_ref = electrode_right << electrode_connector
    electrode_connector_ref.move((-radius + electrode_gap/2, width_wg/2 + wg_gap + width_bend/2 + radius + length_y/2))
    er = c << electrode_right
    el = c << electrode_left
    return Utils.pos_neg_seperate(c)

if __name__ == "__main__":
    c = EO_racetrack(length_x=0, length_y=6000, radius=100, electrode_length_difference=20)
    # c = ring_circle(width_wg = 5, length_extension_left = 500, length_extension_right = 500)
    c.plot()
    c.show()