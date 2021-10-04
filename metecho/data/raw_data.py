import numpy as np
import h5py

class AXIS:
    CHANNEL = 'channel'
    SAMPLE = 'sample'
    PULSE = 'pulse'
    POLARIZATION = 'polarization'


class RawDataInterface:

    def __init__(self):
        self.data = None
        self.axis = None
