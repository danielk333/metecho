import numpy as np
from math import isclose
from metecho.data import raw_data
from metecho.event_search import event_search, conf, search_objects, filters
from metecho.generalized_matched_filter import signal_model
from unittest.mock import patch, mock_open, MagicMock, Mock


def test_search_object():
    class TestSearch(search_objects.SearchObject):
        def search(self, matched_filter_output, raw_data):
            return self.arguments["test"]
    searcher = TestSearch(test=True)
    assert searcher.search(None, None)


def test_conf_file_read():
    data = "[General]\nTestValue = 132"
    with patch("builtins.open", mock_open(read_data=data)) as mock_file:
        mock_file.is_file = MagicMock(return_value=True)
        configuration = conf.generate_event_search_config(file_input=mock_file)
        assert configuration['General']['TestValue'] == '132'


def test_gaussian_noise():
    test_data = raw_data.RawDataInterface(None, load_on_init=False)
    reals = np.zeros([1, 10, 10], dtype=np.float64)
    imags = np.ones([1, 10, 10], dtype=np.float64)
    test_data.data = reals + imags * 1j
    test_data.axis['channel'] = 0
    test_data.axis['sample'] = 1
    test_data.axis['pulse'] = 2
    gaussian_filter = filters.CalculateGaussianNoise()
    return_value = gaussian_filter.filter(test_data)
    assert return_value["mean"] == 0.5
    assert return_value["std_dev"] == 0.5
    assert isclose(return_value["CI"][0], 0.65, abs_tol=10**-2)
    assert isclose(return_value["CI"][1], 0.39, abs_tol=10**-2)


def test_partial_data_input():
    test_data = raw_data.RawDataInterface(None, load_on_init=False)
    test_data.data = np.zeros([1, 10, 10], dtype=np.complex128)
    test_data.axis['channel'] = 0
    test_data.axis['sample'] = 1
    test_data.axis['pulse'] = 2
    test_filter_output = {
        'powmaxall': np.ones([36, 5], dtype=np.complex128),
        'sample_length': 10,
        'pulse_length': 5
    }
    configuration = conf.generate_event_search_config()
    configuration["General"]["MOVE_STD_WINDOW"] = "2"
    signal = signal_model.barker_code_13(test_data.data.shape[1], 2)

    class TestSearch(search_objects.SearchObject):
        def search(self, matched_filter_output, raw_data):
            if (matched_filter_output["powmaxall"].shape == (36, 10)
                and matched_filter_output["sample_length"] == 10
                    and matched_filter_output["pulse_length"] == 10):
                return True
            return False
    searcher = TestSearch()
    result = event_search.search(test_data, configuration, test_filter_output, [searcher], signal)
    assert result[0]


def test_event_search_functionality():
    result = np.zeros(100, dtype=bool)

    class TestSearch(search_objects.SearchObject):
        def search(self, matched_filter_output, raw_data):
            return np.zeros(self.arguments["length"], dtype=bool)
    searcher = TestSearch(length=100)
    assert np.array_equal(event_search.search(None, None, None, [searcher], None), [result])


def test_default_config():
    configuration = conf.generate_event_search_config()
    assert configuration['General']['CRITERIA_N'] is not None
    assert configuration['General']['MOVE_STD_WINDOW'] is not None
    assert configuration['General']['FIND_CRITERIA_xcorr_sigma'] is not None
    assert configuration['General']['FIND_CRITERIA_totpow_sigma'] is not None
    assert configuration['General']['FIND_CRITERIA_dop_STD_sigma'] is not None
    assert configuration['General']['FIND_CRITERIA_start_STD_sigma'] is not None
    assert configuration['General']['dop_std_coherr'] is not None
    assert configuration['General']['start_std_coherr'] is not None
    assert configuration['General']['start_std_coherr_percent'] is not None
    assert configuration['General']['dop_std_coherr_percent'] is not None
    assert configuration['General']['pow_std_est'] is not None
    assert configuration['General']['pow_std_filt'] is not None
    assert configuration['General']['FIND_CRITERIA_dop_sigma'] is not None
    assert configuration['General']['FIND_CRITERIA_ind_pm'] is not None
    assert configuration['General']['min_dop_allowed'] is not None
    assert configuration['General']['max_start_allowed'] is not None
    assert configuration['General']['min_start_allowed'] is not None
    assert configuration['General']['least_ipp_avalible'] is not None
    assert configuration['General']['min_ipp_separation_split'] is not None
    assert configuration['General']['min_dop_separation_split'] is not None
    assert configuration['General']['min_range_separation_split'] is not None
    assert configuration['General']['smoothing_window'] is not None
    assert configuration['General']['IPP_extend'] is not None
    assert configuration['General']['allow_analysis_overlap'] is not None
    assert configuration['General']['event_max_overlap'] is not None
