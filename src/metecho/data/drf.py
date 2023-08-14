import logging
# import numpy as np

from . import raw_data

logger = logging.getLogger(__name__)

logger.debug('Importing MPI')
try:
    import digital_rf
except ImportError:
    logger.warning('digital_rf import failed: this raw_data backed is not available')
    digital_rf = None


@raw_data.backend_validator('digital_rf')
def validate_digital_rf(path):
    return False


@raw_data.backend_loader('digital_rf')
def load_digital_rf(path):
    pass
