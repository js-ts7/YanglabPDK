import gdsfactory as gf
import numpy as np
import YanglabPDK.YanglabUtils as Utils
import YanglabPDK.YanglabSections as Sections
from YanglabPDK import LAYER as LAYER

from YanglabPDK.components.couplers.coupler_ring import coupler_halfring
from YanglabPDK.components.bends.bend_circular import bend_circular
from YanglabPDK.components.waveguides.straight import straight

from functools import partial

@gf.cell
def dual_ring_drop_heater(
    gap_wg_top: float = 0.35,
    gap_wg_bottom: float = 0.35,
    gap_ring: float = 0.2,
    radius: float = 10.0,
    width_wg: float = 1,
    width_ring: float = 1.2,
    buffer: float = 3,
    length_extension_left: float = 0.0,
    length_extension_right: float = 0.0,
    heater_width: float = 0.5,
    heater_angle: float = 70.0,
    heater_taper_length: float = 5.0,
    undercut_width: float = 0.0,
    undercut_gap: float = 3.0,
    pad_dx: float = 250.0,
    pad_dy: float = 400.0,
    pad_size: tuple = (200, 200),
    metal_routing_radius: float = 20.0,
    metal_routing_width: float = 30.0,
) -> gf.Component:
    """Returns two identical coupled ring, one point coupled to waveguide."""

    c = gf.Component()

    wg_half_ring_bottom = c << coupler_halfring(
        gap=gap_wg_bottom,
        radius=radius,
        length_x=0.0,
        width_wg=width_wg,
        width_bend=width_ring,
        buffer=buffer,
        length_extension_left=length_extension_left,
        length_extension_right=length_extension_right,
    )

    bottom_ring_right = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)
    bottom_ring_left = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)

    bottom_ring_left.connect(port="o2", other=wg_half_ring_bottom.ports["o2"])
    bottom_ring_right.connect(port="o1", other=wg_half_ring_bottom.ports["o3"])

    top_ring_left = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)
    top_ring_left.mirror_x()
    top_ring_left.movey(radius*2 + gap_ring + width_ring + width_wg + gap_wg_bottom)
    top_ring_right = c << bend_circular(radius=radius, width=width_ring, buffer=buffer)
    top_ring_right.connect(port="o1", other=top_ring_left.ports["o1"])

    wg_half_ring_top = c << coupler_halfring(
        gap=gap_wg_top,
        radius=radius,
        length_x=0.0,
        width_wg=width_wg,
        width_bend=width_ring,
        buffer=buffer,
        length_extension_left=length_extension_left,
        length_extension_right=length_extension_right
    )
    wg_half_ring_top.mirror_y()
    wg_half_ring_top.connect(port="o2", other=top_ring_left.ports["o2"])
    wg_half_ring_top.connect(port="o3", other=top_ring_right.ports["o2"])

    c.add_port("o1", port=wg_half_ring_top.ports["o1"])
    c.add_port("o2", port=wg_half_ring_top.ports["o4"])
    c.add_port("o3", port=wg_half_ring_bottom.ports["o1"])
    c.add_port("o4", port=wg_half_ring_bottom.ports["o4"])

    cross_section = Sections.pos_neg_resist(width=width_ring, buffer=buffer)
    cross_section_heater = partial(gf.cross_section.heater_metal, width=heater_width, layer=LAYER.MT2)
    cross_section_waveguide_heater = partial(gf.cross_section.strip_heater_metal, width=width_ring, 
                                             layer=LAYER.NR, layer_heater=LAYER.MT2, heater_width=heater_width, 
                                             sections=Sections.pos_neg_Section_Tuple(width=width_ring, buffer=buffer))
    cross_section_heater_undercut = partial(gf.cross_section.strip_heater_metal_undercut, layer=LAYER.NR, 
                                            width=undercut_width, heater_width=heater_width, trench_gap=undercut_gap, 
                                            layer_heater=LAYER.MT2, layer_trench=LAYER.DT, trench_width=undercut_width, 
                                            sections=Sections.pos_neg_Section_Tuple(width=undercut_width, buffer=buffer+undercut_gap))
    vs = gf.components.via_stack(size=(11.0, 11.0), layers=[LAYER.MT2, LAYER.MT1], correct_size=True, slot_horizontal=False, 
                                 slot_vertical=False, vias=[None, None])
    metal_crosssec = partial(gf.cross_section.metal_routing, width=metal_routing_width, layer=LAYER.MT1)
    corner_crosssec = partial(gf.cross_section.metal_routing, width=metal_routing_radius, layer=LAYER.MT1)


    heater_bottom_right = c << gf.components.bend_circular_heater(
        radius=radius,
        angle=heater_angle,
        heater_to_wg_distance=0.0,
        heater_width=0.5,
        cross_section=cross_section_heater,
    )
    heater_bottom_right.movey(width_wg/2 + gap_wg_bottom + width_ring/2)
    heater_bottom_right.rotate(angle=20, center=(0, width_wg/2 + gap_wg_bottom + width_ring/2 + radius))
    heater_bottom_left = c << gf.components.bend_circular_heater(
        radius=radius,
        angle=heater_angle,
        heater_to_wg_distance=0.0,
        heater_width=0.5,
        cross_section=cross_section_heater,
    )
    heater_bottom_left.mirror_x()
    heater_bottom_left.movey(width_wg/2 + gap_wg_bottom + width_ring/2)
    heater_bottom_left.rotate(angle=-20, center=(0, width_wg/2 + gap_wg_bottom + width_ring/2 + radius))

    heater_top_right = c << gf.components.bend_circular_heater(
        radius=radius,
        angle=heater_angle,
        heater_to_wg_distance=0.0,
        heater_width=0.5,
        cross_section=cross_section_heater,
    )
    heater_top_right.mirror_y()
    heater_top_right.movey(2*radius + width_ring/2 + gap_wg_bottom + width_wg/2)
    heater_top_right.rotate(angle=-(90-heater_angle+1), center=(0, width_wg/2 + gap_wg_bottom + width_ring/2 + radius))
    heater_top_left = c << gf.components.bend_circular_heater(
        radius=radius,
        angle=heater_angle,
        heater_to_wg_distance=0.0,
        heater_width=0.5,
        cross_section=cross_section_heater,
    )
    heater_top_left.mirror_x()
    heater_top_left.mirror_y()
    heater_top_left.movey(2*radius + width_ring/2 + gap_wg_bottom + width_wg/2)
    heater_top_left.rotate(angle=90-heater_angle+1, center=(0, width_wg/2 + gap_wg_bottom + width_ring/2 + radius))

    heater_connect_top = gf.Component()
    heater_connect_top.add_polygon(
        points=[
            (heater_top_left.ports["e1"].x + heater_width/2*np.cos(heater_angle/180*np.pi), heater_top_left.ports["e1"].y - heater_width/2*np.sin(heater_angle/180*np.pi)),
            (heater_top_left.ports["e1"].x + 10.0, heater_top_left.ports["e1"].y - 20.0),
            (heater_top_right.ports["e1"].x - 10.0, heater_top_right.ports["e1"].y - 20.0),
            (heater_top_right.ports["e1"].x - heater_width/2*np.cos(heater_angle/180*np.pi), heater_top_right.ports["e1"].y - heater_width/2*np.sin(heater_angle/180*np.pi)),
            (heater_top_right.ports["e1"].x - heater_width/2*np.cos(heater_angle/180*np.pi) + heater_width*5.5*np.sin(heater_angle/180*np.pi), heater_top_right.ports["e1"].y - heater_width/2*np.sin(heater_angle/180*np.pi) - heater_width*5.5*np.cos(heater_angle/180*np.pi)),
            (heater_top_right.ports["e1"].x - 10.0, heater_top_right.ports["e1"].y - 30.0),
            (heater_top_left.ports["e1"].x + 10.0, heater_top_left.ports["e1"].y - 30.0),
            (heater_top_left.ports["e1"].x + heater_width/2*np.cos(heater_angle/180*np.pi) - heater_width*5*np.sin(heater_angle/180*np.pi), heater_top_left.ports["e1"].y + heater_width/2*np.sin(heater_angle/180*np.pi) - heater_width*5.5*np.cos(heater_angle/180*np.pi)),

        ],
        layer=LAYER.MT2
    )
    c << heater_connect_top

    heater_connect_left = gf.Component()
    extend_x = np.sqrt(2)*11.0/np.sqrt(5)/np.cos(heater_angle/180*np.pi)
    extend_y = extend_x - 11.0
    heater_connect_left.add_polygon(
        points=[
            (heater_bottom_left.ports["e1"].x - heater_width/2*np.cos(heater_angle/180*np.pi), 
             heater_bottom_left.ports["e1"].y - heater_width/2*np.sin(heater_angle/180*np.pi)),
            (heater_bottom_left.ports["e1"].x - heater_width/2*np.cos(heater_angle/180*np.pi) - heater_width*5*np.sin(heater_angle/180*np.pi), 
             heater_bottom_left.ports["e1"].y - heater_width/2*np.sin(heater_angle/180*np.pi) + heater_width*5.5*np.cos(heater_angle/180*np.pi)),
            (heater_bottom_left.ports["e1"].x - extend_x, heater_bottom_left.ports["e1"].y - extend_y),
            (heater_bottom_left.ports["e1"].x - extend_y, heater_bottom_left.ports["e1"].y - extend_x),
        ],
        layer=LAYER.MT2
    )
    c << heater_connect_left
    heater_connect_right = heater_connect_left.copy().mirror_x()
    c << heater_connect_right

    vs_left = c << vs
    vs_left.move((heater_bottom_left.ports["e1"].x-(extend_x + extend_y)/2, 
                  heater_bottom_left.ports["e1"].y-(extend_x + extend_y)/2))
    pad_left = c << gf.components.pad(size=pad_size, layer=LAYER.MT1)
    pad_left.x = -pad_dx
    pad_left.y = -pad_dy
    metal_corner = partial(gf.components.wire_corner45, cross_section=corner_crosssec)
    metal_taper = partial(gf.components.taper_electrical, cross_section=partial(gf.cross_section.metal_routing, layer=LAYER.MT1))
    pdk = gf.get_active_pdk()
    pdk.layer_transitions[LAYER.MT1] = metal_taper
    gf.routing.route_single(
        c, pad_left.ports["e2"], vs_left.ports["e4"],
        cross_section=metal_crosssec, bend=metal_corner, radius=metal_routing_radius,
        port_type="electrical", allow_width_mismatch=True, auto_taper=True,
        steps=[
            {"dy": 100, "dx": 0},
            {"x": vs_left.ports["e4"].x}
        ]
    )
    
    vs_right = c << vs
    vs_right.move((heater_bottom_right.ports["e1"].x+(extend_x + extend_y)/2, 
                   heater_bottom_right.ports["e1"].y-(extend_x + extend_y)/2))
    pad_right = c << gf.components.pad(size=pad_size, layer=LAYER.MT1)
    pad_right.x = pad_dx
    pad_right.y = -pad_dy
    
    
    gf.routing.route_single(
        c, pad_right.ports["e2"], vs_right.ports["e4"],
        cross_section=metal_crosssec, radius=metal_routing_radius,
        port_type="electrical", allow_width_mismatch=True, auto_taper=True,
        bend=metal_corner,
        steps=[
            {"dy": 100, "dx": 0},
            {"x": vs_right.ports["e4"].x}
        ]
    )

    return Utils.pos_neg_seperate(c)

if __name__ == "__main__":
    c = dual_ring_drop_heater(radius=50)
    c.plot()
    c.show()
