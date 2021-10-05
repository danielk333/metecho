import pathlib

import numpy as np
import h5py

BACKENDS = {}
BACKEND_ERROR = ValueError('Not compatible with backend')

def raw_data_backend(name):
    '''Decorator to automatically register function as a raw-data backend

    Should raise `BACKEND_ERROR` if wrong file format for the backend
    '''

    def backend_wrapper(func):
        global BACKENDS
        BACKENDS[name] = func
        return func

    return backend_wrapper



class RawDataInterface:
    '''Common interface between metecho functionality and different radar-data backends.
    '''

    DATA_AXIS = [
        'channel',
        'sample',
        'pulse',
        'polarization',
    ]

    def __init__(self, path, **kwargs):
        self.path = pathlib.Path(path)

        self.data = None
        self.axis = {key:None for key in self.DATA_AXIS}

        self.load(**kwargs)


    def load(self, **kwargs):
        for backend, load_func in BACKENDS.items():
            try:
                data, data_axis = load_func(path, **kwargs)
            except ValueError:
                continue

            self.data = data
            for axis_name in data_axis:
                self.axis[axis_name] = data_axis.index(axis_name)

        if self.data is None:
            raise ValueError('No backend found for given input path')