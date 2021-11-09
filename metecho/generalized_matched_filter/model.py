import numpy as np


encode = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1],
                  dtype=np.float64)


def getModel(code_name):
    if code_name == "barker":
        return encode

    raise ValueError(f'No model found for {code_name}')
