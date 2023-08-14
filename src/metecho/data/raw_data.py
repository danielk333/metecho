import pathlib
import logging
from collections import OrderedDict

import numpy as np

logger = logging.getLogger(__name__)

BACKENDS = OrderedDict()


def check_if_raw_data(path):
    """Checks if the given path is a supported raw data file and returns the 
    backend if it exists, else returns None.
    """
    for backend, (_, validate) in BACKENDS.items():
        if validate(path):
            return backend
    return None


def backend_loader(name):
    """Decorator to register function as a raw-data backend loader

    #TODO: add descripiton of backend load function here (what it should return ect)
    """

    def backend_wrapper(func):
        logger.debug(f"Registering loader for {name} backend")
        if name in BACKENDS:
            BACKENDS[name][0] = func
        else:
            BACKENDS[name] = [func, None]
        return func

    return backend_wrapper


def backend_validator(name):
    """Decorator to register function as a raw-data backend validator

    #TODO: add descripiton of backend load function here (what it should return ect)
    """

    def backend_wrapper(func):
        logger.debug(f"Registering validator for {name} backend")
        if name in BACKENDS:
            BACKENDS[name][1] = func
        else:
            BACKENDS[name] = [None, func]
        return func

    return backend_wrapper


class RawDataInterface:
    """Common interface between metecho functionality and different radar-data backends."""

    DATA_AXIS = [
        "channel",
        "sample",
        "pulse",
        "polarization",
    ]

    META_KEYS = [
        "start_time",
    ]

    def __init__(self, path, backend=None, load_on_init=True, **kwargs):
        self._clear()
        if path is not None:
            self.path = pathlib.Path(path)
        self.backend = backend
        if load_on_init:
            self.load(**kwargs)

    def _clear(self):
        self.data = None
        self.axis = {key: None for key in self.DATA_AXIS}
        self.meta = {key: None for key in self.META_KEYS}

    def load(self, **kwargs):
        self._clear()

        if self.backend is None:
            backend_found = False

            for backend, (load_func, validate) in BACKENDS.items():
                if validate(self.path):
                    data, axis, meta = load_func(self.path, **kwargs)
                    backend_found = True
                    self.backend = backend
                else:
                    continue

                break

            if not backend_found:
                raise ValueError("No backend found for given input path")
        else:
            if self.backend not in BACKENDS:
                raise ValueError(f"Given backend {self.backend} does not exist")

            load_func, validate = BACKENDS[self.backend]
            if validate(self.path):
                data, axis, meta = load_func(self.path, **kwargs)
            else:
                raise ValueError(
                    f"Given backend {self.backend} does not validate input path"
                )

        if not isinstance(data, np.ndarray):
            raise ValueError(
                f'Backend must return data as a numpy ndarray not "{type(data)}"'
            )

        self.data = data
        self.meta.update(meta)
        self.axis.update(axis)

    def copy(self):
        '''Return a copy of the current instance.
        '''
        return RawDataInterface(
            data = self.data.copy,
            axis = copy.deepcopy(self.axis),
            meta = copy.deepcopy(self.meta),
        )
