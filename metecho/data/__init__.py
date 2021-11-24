'''
# Data input sub-package

This sub-package allows loading of data from different 
sources into a unified format that can be used with the 
rest of the package.

## Conventions for saving to h5 file

- dates and time are saved in numpy.datetime64[ns]
- the voltage data nd-array is saved in a dataset called "/data"

'''

from . import mu
from .raw_data import RawDataInterface
from .data_store import directory_tree
from .data_store import RawDataInterfaceFactory
from .data_store import DataStore