"""YanglabPDK public package interface.

This package provides lab-specific layer definitions, cross sections, utilities,
and reusable photonic components on top of gdsfactory.  The top-level namespace
keeps the most frequently used modules available as:

- `YanglabPDK.LAYER`
- `YanglabPDK.Utils`
- `YanglabPDK.Sections`
"""

from YanglabPDK import YanglabLayerStack as LayerStack

LAYER = LayerStack.YanglabLayerMap
__version__ = "0.1.0"

from YanglabPDK import YanglabUtils as Utils
from YanglabPDK import YanglabSections as Sections

__all__ = [
    "LAYER",
    "Utils",
    "Sections",
    "__version__",
]
