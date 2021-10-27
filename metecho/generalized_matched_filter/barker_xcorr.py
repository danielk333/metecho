import ctypes
import os
import logging
import h5py
import numpy as np
import numpy.ctypeslib as npct

logger = logging.getLogger(__name__)

np_double = npct.ndpointer(np.float64, ndim=1, flags='aligned, contiguous, writeable')
np_complex = npct.ndpointer(complex, ndim=1, flags='aligned, contiguous, writeable')
np_int_pointer = npct.ndpointer(np.int32, ndim=1, flags='aligned, contiguous, writeable')


def barker_xcorr_echo_search(raw_data, code=0, xcorr_noise_limit=0.5):
    """
    # Will take a raw_data object and search for signs of a meteor echo.
    # At the moment takes a file location for testing purposes.
    """
    h5file = h5py.File(raw_data, 'r')
    ampsum_all = np.squeeze(np.sum(h5file["data"], 0))
    bestpeak = np.zeros(len(ampsum_all))
    best_dop = np.zeros(len(ampsum_all))
    best_start = np.zeros(len(ampsum_all))
    # powmaxall = zeros([ampsum_size + code_size, ])

    for x in range(0, len(ampsum_all)):
        ampsum = ampsum_all[x, :]
        ampsum_size = len(ampsum)
        code_size = len(code)
        dfvar_size = 351
        pows = np.zeros([dfvar_size * (ampsum_size + code_size)], dtype=complex)
        pows_size = np.array([dfvar_size, ampsum_size + code_size], dtype=np.int32)
        powmax = np.zeros([dfvar_size], dtype=complex)
        powmax_size = dfvar_size
        maxpowind = np.zeros([dfvar_size], dtype=np.int32)
        maxpowind_size = dfvar_size
        samp = np.float64(6E-6)
        libecho.barker_xcorr_echo_search(ampsum,
                                         ampsum_size,
                                         code,
                                         code_size,
                                         pows,
                                         pows_size,
                                         powmax,
                                         powmax_size,
                                         maxpowind,
                                         maxpowind_size,
                                         samp)
        print(maxpowind)


# We start by making a path to the current directory.
script_dir = os.path.dirname(os.path.realpath(__file__))
# Then we open the created shared libecho file
libecho = ctypes.CDLL(script_dir + "/libecho.so")
libecho.barker_xcorr_echo_search.argtypes = [np_complex,
                                             ctypes.c_int,
                                             np_double,
                                             ctypes.c_int,
                                             np_complex,
                                             np_int_pointer,
                                             np_complex,
                                             ctypes.c_int,
                                             np_int_pointer,
                                             ctypes.c_int,
                                             ctypes.c_double]

encode = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1],
                  dtype=np.float64)
barker_xcorr_echo_search("/mnt/e/Kurser/X7007E/data/2009/06/27/2009-06-27T09.54.05.690000000.h5", code=encode)


"""
libecho.get_complex_number.argtypes = [np_int_pointer]
libecho.get_complex_number.restype = np_complex_2d

size = np.array([10, 10], dtype=np.int32)

array = libecho.get_complex_number(size)

a = npct.as_array(array, shape=(size[0] * size[1],))

print(a)
"""
"""
dfvar_size=351
ampsum = np.zeros(100, dtype=complex)
code_size = len(code)
ampsum[0:0+code_size] = np.array(code, dtype=complex)
ampsum_size = len(ampsum)
pows = np.zeros([dfvar_size * (ampsum_size + code_size)], dtype=complex)
pows_size = np.array([dfvar_size, ampsum_size + code_size], dtype=np.int32)
powmax = np.zeros([dfvar_size], dtype=complex)
powmax_size = dfvar_size
maxpowind = np.zeros([dfvar_size], dtype=np.int32)
maxpowind_size = dfvar_size
samp = np.float64(6E-6)
libecho.barker_xcorr_echo_search(ampsum, ampsum_size, code, code_size, pows, pows_size, powmax, powmax_size, maxpowind, maxpowind_size, samp)
pows.shape = (pows.size//pows_size[1], pows_size[1])
"""
# Call the function! Note that strings must use 'b' or else it will
# only get the first byte of data.

# We then create a pointer type -- it represents how our function works, kind of
# how like you declare a function in a header file.
# c_function_pointer_type = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
# Create a pointer to a function that matches those types (in this case)
# a function called "printstring"
# callback = c_function_pointer_type(printstring)
# Set the argument types for the receiving function (so it knows what kind of
# data it will receive)
