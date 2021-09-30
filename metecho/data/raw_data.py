import numpy as np
import h5py

class RawData:

    def __init__(self, path):
        self.file = h5py.File(path, 'r')

    def validate(self):
        pass
