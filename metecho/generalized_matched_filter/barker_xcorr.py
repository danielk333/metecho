import ctypes
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

script_dir = os.path.dirname(os.path.realpath(__file__))
testlib = ctypes.CDLL(script_dir + "/testlib.so")
testlib.myprint.argtypes = [ctypes.c_float, ctypes.c_float]
a = 8 + 24 * 1j
testlib.myprint(np.real(a), np.imag(a))
