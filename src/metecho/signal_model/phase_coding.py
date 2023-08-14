import numpy as np


barker13 = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
                    dtype=np.float64)


def barker_code_13(pulse_amount, oversampling):
    return_value = np.tile(np.kron(barker13, np.ones(oversampling)), pulse_amount)
    return_value.shape = (pulse_amount, 13 * oversampling)
    return return_value
