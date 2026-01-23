"""Project that controls and measures a muon telescope."""

from . import measurement
from ._version import __version__
from .telescope import Telescope

__all__ = [
    "__version__",
    "Telescope",
    "measurement",
]
