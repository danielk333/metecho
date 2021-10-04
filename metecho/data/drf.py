import logging
import numpy as np

logger = logging.getLogger(__name__)

logger.debug('Importing MPI')
try:
    import digital_rf
except ImportError:
    logger.warning('digital_rf import failed: this raw_data backed is not available')
    digital_rf = None

