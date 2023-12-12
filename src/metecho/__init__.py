'''Analysis of meteors in radar data.

'''
import sysconfig
import pathlib
import ctypes

# Load the C-lib
suffix = sysconfig.get_config_var('EXT_SUFFIX')
if suffix is None:
    suffix = ".so"

# We start by making a path to the current directory.
pymodule_dir = pathlib.Path(__file__).resolve().parent 
__libpath__ = pymodule_dir / ('clibmet' + suffix)

# Then we open the created shared libecho file
libmet = ctypes.cdll.LoadLibrary(__libpath__)

# Expose package upon import
from .version import __version__

from . import tools
from . import data
from . import plot
from . import events
from . import meteoroid_streams
from . import meteor_model
from . import signal_model
from . import simulation
from . import coordinates
from . import estimation

from .tools import profiling
