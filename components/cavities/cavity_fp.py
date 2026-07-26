import gdsfactory as gf

from YanglabPDK import YanglabUtils as Utils
from YanglabPDK import YanglabSections as Sections
from YanglabPDK.components.couplers.coupler import coupler as coupler_component
from YanglabPDK.components.filters.dbr import dbr as dbr_component

@gf.cell
def cavity_fp(dbr=None, coupler=None):
    """Return a Fabry-Perot cavity assembled from DBR and coupler cells."""
    if dbr is None:
        dbr = dbr_component(w1=1, w2=0.5, n=20)
    if coupler is None:
        coupler = coupler_component(dy=8, dx=20)

    c = gf.Component()
    cr = c << coupler
    ml = c << dbr
    mr = c << dbr

    ml.connect(port="o1", other=cr.ports["o2"])
    mr.connect(port="o1", other=cr.ports["o3"])
    c.add_port("o1", port=cr.ports["o1"])
    c.add_port("o2", port=cr.ports["o4"])
    c.copy_child_info(dbr)
    return c

if __name__ == "__main__":
    c = cavity_fp()
    c.draw_ports()
    c.show()
