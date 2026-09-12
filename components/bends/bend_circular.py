import gdsfactory as gf

from YanglabPDK import YanglabUtils as Utils
from YanglabPDK import YanglabSections as Sections


def _to_component(component):
    if not isinstance(component, gf.ComponentAllAngle):
        return component

    flattened = gf.Component()
    flattened.add_ref_off_grid(component)
    for port in component.ports:
        flattened.add_port(name=port.name, port=port)
    flattened.flatten()
    return flattened

@gf.cell
def bend_circular(
    radius: float = 100, 
    angle: float = 90, 
    width: float = 1, 
    buffer: float = 3
) -> gf.Component:
    """Returns a radial arc.

    Args:
        radius: in um. Defaults to cross_section_radius.
        angle: angle of arc (degrees).
        width: width to use. Defaults to cross_section.width.
        buffer: buffer width for positive tone resist (um)
    
    Returns:
        Component with the generated layout.
    """
    if angle in (90, 180):
        component = gf.components.bend_circular(
            radius=radius,
            angle=angle,
            cross_section=Sections.pos_neg_resist(width=width, buffer=buffer),
        )
    else:
        component = gf.components.bend_circular_all_angle(
            radius=radius,
            angle=angle,
            cross_section=Sections.pos_neg_resist(width=width, buffer=buffer),
        )

    c = Utils.pos_neg_seperate(_to_component(component))
    c.locked = False
    c.flatten()
    return c

if __name__ == "__main__":
    c = bend_circular(radius=100)
    c.show()
