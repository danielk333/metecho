import ctypes
import logging
import numpy as np
import numpy.ctypeslib as npct
from pathlib import Path

logger = logging.getLogger(__name__)

np_double = npct.ndpointer(np.float64, ndim=1, flags='aligned, contiguous, writeable')
np_complex = npct.ndpointer(np.complex128, ndim=1, flags='aligned, c_contiguous, writeable')
np_complex_2d = npct.ndpointer(np.complex128, ndim=2, flags='aligned, c_contiguous, writeable')
np_complex_single = npct.ndpointer(np.complex128, ndim=0)
np_int_pointer = npct.ndpointer(np.int32, ndim=1, flags='aligned, contiguous, writeable')

# We start by making a path to the current directory.
script_dir = Path(__file__).resolve().parent  # os.path.dirname(os.path.realpath(__file__))
libecho_location = list(Path(script_dir).glob('libecho.*.so'))
# Then we open the created shared libecho file
libecho = ctypes.CDLL(libecho_location[0])
libecho.xcorr_echo_search.argtypes = [
    ctypes.c_double,
    ctypes.c_double,
    ctypes.c_double,
    np_complex,
    ctypes.c_int,
    np_double,
    ctypes.c_int,
    np_complex_2d,
    np_complex_2d,
    np_int_pointer,
    np_complex,
    ctypes.c_int,
    np_int_pointer,
    ctypes.c_int,
    ctypes.c_double,
]


def xcorr_echo_search(
    raw_data,
    doppler_freq_min,
    doppler_freq_max,
    doppler_freq_step,
    signal_model,
):
    """
    # Will take a raw_data object and search for signs of a meteor echo.
    # At the moment takes a file location for testing purposes.
    """
    matched_filter_output = {}
    index_finish = 0
    sample_signal_all = np.sum(raw_data.data, 0)
    doppler_freq_size = int(((doppler_freq_max - doppler_freq_min) / doppler_freq_step) + 1)
    if len(signal_model.shape) == 1:
        signal_model.shape = (1, signal_model.size)
    signal_model_size = signal_model.shape[1]
    best_peak = np.zeros(sample_signal_all.shape[1], dtype=np.complex128)
    best_start = np.zeros(sample_signal_all.shape[1])
    best_doppler = np.zeros(sample_signal_all.shape[1])
    powmaxall = np.zeros(
        [sample_signal_all.shape[0] + signal_model_size,
         sample_signal_all.shape[1]],
        dtype=np.complex128
    )
    powmaxall_norm = np.zeros(
        [sample_signal_all.shape[0] + signal_model_size,
         sample_signal_all.shape[1]],
        dtype=np.complex128
    )

    samp = np.float64(6E-6)
    logger.debug("Starting crosscorrelation echo search cycle.")
    for x in range(0, sample_signal_all.shape[1]):
        sample_signal = sample_signal_all[:, x].copy()
        sample_signal_size = len(sample_signal)
        pows = np.zeros([doppler_freq_size, (sample_signal_size + signal_model_size)], dtype=np.complex128)
        pows_normalized = np.zeros(
            [doppler_freq_size, (sample_signal_size + signal_model_size)],
            dtype=np.complex128
        )
        pows_size = np.array([doppler_freq_size, sample_signal_size + signal_model_size], dtype=np.int32)
        powmax = np.zeros([doppler_freq_size], dtype=np.complex128)
        powmax_size = doppler_freq_size
        maxpowind = np.zeros([doppler_freq_size], dtype=np.int32)
        maxpowind_size = doppler_freq_size
        logger.debug("Calling C function.")
        libecho.xcorr_echo_search(
            doppler_freq_min,
            doppler_freq_max,
            doppler_freq_step,
            sample_signal,
            sample_signal_size,
            signal_model[x],
            signal_model_size,
            pows,
            pows_normalized,
            pows_size,
            powmax,
            powmax_size,
            maxpowind,
            maxpowind_size,
            samp,
        )
        powmaxall[:, x] = np.max(pows, axis=0)
        powmaxall_norm[:, x] = np.max(pows_normalized, axis=0)
        best_value_index = np.argmax(powmax)
        best_peak[x] = powmax[best_value_index]
        best_start[x] = maxpowind[best_value_index]
        best_doppler[x] = doppler_freq_min + (best_value_index * doppler_freq_step)
    matched_filter_output["powmaxall"] = powmaxall
    matched_filter_output["powmaxall_norm"] = powmaxall_norm
    matched_filter_output["best_peak"] = best_peak
    matched_filter_output["best_start"] = best_start
    matched_filter_output["best_doppler"] = best_doppler
    matched_filter_output["sample_length"] = sample_signal_all.shape[0]
    matched_filter_output["pulse_length"] = sample_signal_all.shape[1]
    return matched_filter_output


def crosscorrelate(x, y, min_delay, max_delay):
    """
    Crosscorrelates two arrays between a max and a min delay. Does not normalize them.
    """
    return_value = np.zeros([len(x) + len(y)], dtype=np.complex128)
    libecho.crosscorrelate(
        x,
        len(x),
        y,
        len(y),
        min_delay,
        max_delay,
        return_value,
    )
    return return_value


def crosscorrelate_single_delay(x, y, delay):
    """
    Crosscorrelates over a single delay. Does not normalize.
    """
    return_value = np.zeros([1], dtype=np.complex128)
    libecho.crosscorrelate_single_delay(
        x,
        len(x),
        y,
        len(y),
        delay,
        return_value
    )
    return return_value


def set_norm_coefs(abs_signal_sample_sum, start, stop, inarray):
    libecho.set_norm_coefs(abs_signal_sample_sum, start, stop, inarray)
    return inarray


def elementwise_cabs_square(inarray, start, stop):
    result = np.zeros([stop - start], dtype=np.complex128)
    libecho.elementwise_cabs_square(inarray, start, stop, result)
    return result


def arange(start, stop, step):
    outarray = np.zeros([int((stop - start) / step) + 1], dtype=np.double)
    libecho.arange(start, stop, step, outarray)
    return outarray


libecho.crosscorrelate.argtypes = [
    np_complex,
    ctypes.c_int,
    np_complex,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    np_complex,
]

libecho.crosscorrelate_single_delay.argtypes = [
    np_complex,
    ctypes.c_int,
    np_complex,
    ctypes.c_int,
    ctypes.c_int,
    np_complex,
]

libecho.set_norm_coefs.argtypes = [
    np_complex_single,
    ctypes.c_int,
    ctypes.c_int,
    np_complex,
]

libecho.elementwise_cabs_square.argtypes = [
    np_complex,
    ctypes.c_int,
    ctypes.c_int,
    np_complex
]

libecho.arange.argtypes = [
    ctypes.c_double,
    ctypes.c_double,
    ctypes.c_double,
    np_double,
]
