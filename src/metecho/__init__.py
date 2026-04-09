"""Analysis of meteors in radar data."""

import ctypes
import pathlib
import sysconfig

from . import (
    coordinates,
    estimation,
    events,
    meteor_model,
    meteoroid_streams,
    plot,
    simulation,
    tools,
)
from .tools import profiling

# Expose package upon import
from .version import __version__
