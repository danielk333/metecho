import logging

import numpy as np

from . import raw_data

logger = logging.getLogger(__name__)

logger.debug("Importing MPI")
try:
    import digital_rf as drf
except ImportError:
    logger.debug("digital_rf import failed: this raw_data backed is not available")
    drf = None


@raw_data.backend_validator("eiscat_digital_rf")
def validate_digital_rf(path):
    return path.exists()


@raw_data.backend_loader("eiscat_digital_rf")
def load_digital_rf(path, channel="rx", pulses=512, ipp=1.5e-3, samples_per_pulse=0):
    do = drf.DigitalRFReader(str(path))
    channels = do.get_channels()
    if channel not in channels:
        raise ValueError(f"Channel '{channel}' not in channels... choose from:\n{channels}")
    start_s, end_s = do.get_bounds(channel)
    props = do.get_properties(channel)
    samps_p_s = props["samples_per_second"]
    ipp_samps = ipp*samps_p_s
    data = np.empty((1, samples_per_pulse, pulses), dtype=np.complex64)
    offset = start_s
    for ind in range(pulses):
        _d = do.read_vector_1d(offset, samples_per_pulse, channel)
        data[0, :, ind] = _d.astype('c8', casting='unsafe', copy=False)
        offset += ipp_samps

    meta = {}
    meta["filename"] = str(path)

    return data, {"channel": 0, "sample": 1, "pulse": 2}, meta
