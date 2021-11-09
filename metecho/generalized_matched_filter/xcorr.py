import ctypes
import os
import logging
import numpy as np
import numpy.ctypeslib as npct

logger = logging.getLogger(__name__)

np_double = npct.ndpointer(np.float64, ndim=1, flags='aligned, contiguous, writeable')
np_complex = npct.ndpointer(np.complex128, ndim=1, flags='aligned, c_contiguous, writeable')
np_complex_2d = npct.ndpointer(np.complex128, ndim=2, flags='aligned, c_contiguous, writeable')
np_complex_single = npct.ndpointer(np.complex128, ndim=0)
np_int_pointer = npct.ndpointer(np.int32, ndim=1, flags='aligned, contiguous, writeable')

encode = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1],
                  dtype=np.float64)


# We start by making a path to the current directory.
script_dir = os.path.dirname(os.path.realpath(__file__))
# Then we open the created shared libecho file
libecho = ctypes.CDLL(script_dir + "/libecho.so")
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


def barker_xcorr_echo_search(
    raw_data,
    doppler_freq_min,
    doppler_freq_max,
    doppler_freq_step,
    code=encode,
    xcorr_noise_limit=0.5,
):
    """
    # Will take a raw_data object and search for signs of a meteor echo.
    # At the moment takes a file location for testing purposes.
    """
    sample_signal_all = np.squeeze(np.sum(raw_data["data"], 0))
    code_size = len(code)
    doppler_freq_size = int(((doppler_freq_max - doppler_freq_min) / doppler_freq_step) + 1)
    best_peak = np.zeros(sample_signal_all.shape[1], dtype=np.complex128)
    best_start = np.zeros(sample_signal_all.shape[1])
    best_doppler = np.zeros(sample_signal_all.shape[1])
    powmaxall = np.zeros(
        [sample_signal_all.shape[0] + code_size,
         sample_signal_all.shape[1]],
        dtype=np.complex128
    )
    samp = np.float64(6E-6)
    logger.debug("Starting crosscorrelation echo search cycle.")
    for x in range(0, sample_signal_all.shape[1]):
        sample_signal = sample_signal_all[:, x].copy()
        sample_signal_size = len(sample_signal)
        pows = np.zeros([doppler_freq_size, (sample_signal_size + code_size)], dtype=np.complex128)
        pows_normalized = np.zeros([doppler_freq_size, (sample_signal_size + code_size)], dtype=np.complex128)
        pows_size = np.array([doppler_freq_size, sample_signal_size + code_size], dtype=np.int32)
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
            code,
            code_size,
            pows,
            pows_normalized,
            pows_size,
            powmax,
            powmax_size,
            maxpowind,
            maxpowind_size,
            samp,
        )
        powmaxall[:, x] = np.max(pows_normalized, axis=0)
        best_peak[x] = np.amax(powmax)
        best_value_index = np.where(powmax == best_peak[x])
        best_start[x] = maxpowind[best_value_index]
        best_doppler[x] = doppler_freq_min + (best_value_index[0][0] * doppler_freq_step)
        """
        for x in powmaxall[:, x]:
            if np.abs(x) > xcorr_noise_limit:
                print(x)
        """
    return powmaxall


def crosscorrelate(x, y, min_delay, max_delay):
    libecho.crosscorrelate.argtypes = [
        np_complex,
        ctypes.c_int,
        np_complex,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        np_complex,
    ]
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
    libecho.crosscorrelate_single_delay.argtypes = [
        np_complex,
        ctypes.c_int,
        np_complex,
        ctypes.c_int,
        ctypes.c_int,
        np_complex,
    ]
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
    libecho.set_norm_coefs.argtypes = [
        np_complex_single,
        ctypes.c_int,
        ctypes.c_int,
        np_complex,
    ]
    libecho.set_norm_coefs(abs_signal_sample_sum, start, stop, inarray)
    return inarray


def elementwise_cabs_square(inarray, start, stop):
    libecho.elementwise_cabs_square.argtypes = [
        np_complex,
        ctypes.c_int,
        ctypes.c_int,
        np_complex
    ]
    result = np.zeros([stop - start], dtype=np.complex128)
    libecho.elementwise_cabs_square(inarray, start, stop, result)
    return result


def arange(start, stop, step):
    libecho.arange.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        np_double,
    ]
    outarray = np.zeros([int((stop - start) / step) + 1], dtype=np.double)
    libecho.arange(start, stop, step, outarray)
    return outarray


"""
def complex_sum(inarray):
    libecho.complex_sum.argtypes = [
        np_complex,
        ctypes.c_int,
    ]
    libecho.complex_sum.restype = np_double
    temp = libecho.complex_sum(inarray, len(inarray))
    rv = npct.as_array(temp, shape=(2, ))
    print(rv)
    return rv
"""

"""
dfvar_size=351
ampsum = np.zeros(85, dtype=complex)
code_size = len(encode)
ampsum[44:44+code_size] = np.array(encode, dtype=complex)
ampsum_size = len(ampsum)
pows = np.zeros([dfvar_size, (ampsum_size + code_size)], dtype=complex)
pows_size = np.array([dfvar_size, ampsum_size + code_size], dtype=np.int32)
powmax = np.zeros([dfvar_size], dtype=complex)
powmax_size = dfvar_size
maxpowind = np.zeros([dfvar_size], dtype=np.int32)
maxpowind_size = dfvar_size
samp = np.float64(6E-6)
libecho.barker_xcorr_echo_search(ampsum, ampsum_size, encode, code_size, pows, pows_size, powmax, powmax_size, maxpowind, maxpowind_size, samp)
pows.shape = (pows.size//pows_size[1], pows_size[1])
import matplotlib.pyplot as plt
plt.style.use('classic')
plt.pcolormesh(np.abs(pows))
plt.colorbar()
plt.ylabel('doppler frequency')
plt.xlabel('delay')
plt.savefig('./plot.png')
plt.close('all')
"""

"""
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    encode = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1],
                      dtype=np.float64)
    powsum = barker_xcorr_echo_search(
        "/mnt/e/Kurser/X7007E/data/2009/06/27/2009-06-27T09.54.05.690000000.h5", code=encode)
    plt.style.use('classic')
    plt.pcolormesh(np.abs(powsum))
    plt.colorbar()
    plt.ylabel('signal strength')
    plt.xlabel('time')
    plt.savefig('./plot.png')
    plt.close('all')
"""
