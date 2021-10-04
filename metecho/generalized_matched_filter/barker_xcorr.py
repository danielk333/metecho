import ctypes
import os
import logging

logger = logging.getLogger(__name__)

script_dir = os.path.dirname(os.path.realpath(__file__))
testlib = ctypes.CDLL(script_dir + "/testlib.so")
testlib.myprint()
