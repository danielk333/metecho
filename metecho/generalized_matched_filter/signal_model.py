import numpy as np


barker13 = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
                    dtype=np.complex128)


def barker_code_13(pulse_amount, scale):
    return_value = np.tile(np.kron(barker13, np.ones(scale)), pulse_amount)
    return_value.shape = (pulse_amount, 13 * scale)
    return return_value
