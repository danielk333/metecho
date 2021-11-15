import numpy as np
from metecho.event_search import base


def test_base_functionality():
    test_value = np.zeros(100, dtype=np.complex128)
    result = np.zeros(100, dtype=bool)
    assert np.array_equal(base.search(test_value, test_value, test_value, test_value, test_value), result)
