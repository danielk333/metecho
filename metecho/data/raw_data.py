import pathlib

import numpy as np
import h5py


BACKENDS = {}
BACKEND_ERROR = ValueError('Not compatible with backend')


def raw_data_backend(name):
    '''Decorator to automatically register function as a raw-data backend

    Should raise `BACKEND_ERROR` if wrong file format for the backend.

    #TODO: add descripiton of backend load function here (what it should return ect)
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

    META_KEYS = [
        'start_time',
    ]

    def __init__(self, path, **kwargs):
        self.path = pathlib.Path(path)
        self.backend = None
        self.load(**kwargs)


    def _clear(self):
        self.data = None
        self.axis = {key:None for key in self.DATA_AXIS}
        self.meta = {key:None for key in self.META_KEYS}


    def load(self, **kwargs):
        self._clear()

        for backend, load_func in BACKENDS.items():
            #add better exception logging and catching
            try:
                data, axis, meta = load_func(self.path, **kwargs)
            except ValueError:
                continue

            if not isinstance(data, np.ndarray):
                raise ValueError(f'Backend must return data as a numpy ndarray not "{type(data)}"')

            self.backend = backend

            self.data = data
            self.meta.update(meta)
            self.axis.update(axis)
            break

        if self.data is None:
            raise ValueError('No backend found for given input path')