import ctypes
import os
import logging
import h5py
import numpy as np
import numpy.ctypeslib as npct

logger = logging.getLogger(__name__)

np_double = npct.ndpointer(np.float64, ndim=1, flags='aligned, contiguous, writeable')
np_complex = npct.ndpointer(np.complex128, ndim=1, flags='aligned, c_contiguous, writeable')
np_complex_2d = npct.ndpointer(np.complex128, ndim=2, flags='aligned, c_contiguous, writeable')
np_int_pointer = npct.ndpointer(np.int32, ndim=1, flags='aligned, contiguous, writeable')


def barker_xcorr_echo_search(raw_data, code=0, xcorr_noise_limit=0.5):
    """
    # Will take a raw_data object and search for signs of a meteor echo.
    # At the moment takes a file location for testing purposes.
    """
    h5file = h5py.File(raw_data, 'r')
    raw_data = h5file["data"]
    sample_signal_all = np.squeeze(np.sum(raw_data, 0))
    code_size = len(code)
    doppler_freq_min = -35000.0
    doppler_freq_max = 5000.0
    doppler_freq_step = 100.0
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
        libecho.barker_xcorr_echo_search(
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


# We start by making a path to the current directory.
script_dir = os.path.dirname(os.path.realpath(__file__))
# Then we open the created shared libecho file
libecho = ctypes.CDLL(script_dir + "/libecho.so")
libecho.barker_xcorr_echo_search.argtypes = [
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

encode = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1],
                  dtype=np.float64)
# barker_xcorr_echo_search("/mnt/e/Kurser/X7007E/data/2009/06/27/2009-06-27T09.54.05.690000000.h5", code=encode)

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


if __name__ == '__main__':
    import matplotlib.pyplot as plt
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
"""
