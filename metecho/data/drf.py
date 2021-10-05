import logging
import numpy as np

logger = logging.getLogger(__name__)

logger.debug('Importing MPI')
try:
    import digital_rf
except ImportError:
    logger.warning('digital_rf import failed: this raw_data backed is not available')
    digital_rf = None

from .raw_data import BACKEND_ERROR, raw_data_backend


@raw_data_backend('digital_rf')
def load_digital_rf(path):
    try:
        h5file = h5py.File(file, 'r')
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        raise BACKEND_ERROR

    if 'data' not in h5file or 'beams' not in h5file:
        raise BACKEND_ERROR

    return fh.data[()], ['channel', 'sample', 'pulse']
