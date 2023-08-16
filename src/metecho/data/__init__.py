'''
Data input sub-package
======================

This sub-package allows loading of data from different 
sources into a unified format that can be used with the 
rest of the package.

'''

from . import mu
from . import eiscat_drf
from . import eiscat_matlab
from .raw_data import RawDataInterface, check_if_raw_data
from .data_store import directory_tree
from .data_store import RawDataInterfaceFactory
from .data_store import DataStore
from .converters import convert, check_if_convertable
from .converters import list_converters
