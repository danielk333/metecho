import numpy as np
from metecho.generalized_matched_filter import barker_xcorr


def test_crosscorrelate_single_delay():
    encode = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1],
                      dtype=complex)
    sample_signal = np.zeros(85, dtype=complex)
    sample_signal[23:23 + len(encode)] = encode
    assert barker_xcorr.crosscorrelate_single_delay(sample_signal, encode, -23) == 26


def test_crosscorrelate():
    encode = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1],
                      dtype=complex)
    result = np.array([0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 1 + 0 * 1j,
                       2 + 0 * 1j, 1 + 0 * 1j, 0 + 0 * 1j, 1 + 0 * 1j, 2 + 0 * 1j,
                       1 + 0 * 1j, 0 + 0 * 1j, 1 + 0 * 1j, 2 + 0 * 1j, 1 + 0 * 1j,
                       0 + 0 * 1j, 1 + 0 * 1j, 2 + 0 * 1j, 1 + 0 * 1j, 0 + 0 * 1j,
                       1 + 0 * 1j, 2 + 0 * 1j, 1 + 0 * 1j, 0 + 0 * 1j, 1 + 0 * 1j,
                       2 + 0 * 1j, 1 + 0 * 1j, 0 + 0 * 1j, 13 + 0 * 1j, 26 + 0 * 1j,
                       13 + 0 * 1j, 0 + 0 * 1j, 1 + 0 * 1j, 2 + 0 * 1j, 1 + 0 * 1j,
                       0 + 0 * 1j, 1 + 0 * 1j, 2 + 0 * 1j, 1 + 0 * 1j, 0 + 0 * 1j,
                       1 + 0 * 1j, 2 + 0 * 1j, 1 + 0 * 1j, 0 + 0 * 1j, 1 + 0 * 1j,
                       2 + 0 * 1j, 1 + 0 * 1j, 0 + 0 * 1j, 1 + 0 * 1j, 2 + 0 * 1j,
                       1 + 0 * 1j, 0 + 0 * 1j, 1 + 0 * 1j, 2 + 0 * 1j, 1 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j, 0 + 0 * 1j,
                       ])
    sample_signal = np.zeros(85, dtype=complex)
    sample_signal[23:23 + len(encode)] = encode
    rv = barker_xcorr.crosscorrelate(
        sample_signal,
        encode,
        -len(sample_signal),
        len(encode),
    )
    assert np.array_equal(rv, result)


def test_set_norm_coefs():
    abs_signal_sample_sum = np.array(100 + 0 * 1j, dtype=np.complex128)
    inarray = np.zeros([100], dtype=np.complex128)
    result = np.zeros([100], dtype=np.complex128)
    start = 10
    stop = 20
    result[start:stop] = abs_signal_sample_sum
    rv = barker_xcorr.set_norm_coefs(
        abs_signal_sample_sum,
        start,
        stop,
        inarray,
    )
    assert np.array_equal(rv, result)

"""
def test_complex_sum():
    test_array = np.ones([100], dtype=np.complex128)
    assert barker_xcorr.complex_sum(test_array) == 100
"""