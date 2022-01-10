import numpy as np
from math import isclose
from metecho.data import raw_data
from metecho.events import event_search, conf, search_objects
from metecho.generalized_matched_filter import signal_model
from metecho.noise import calc_noise
from unittest.mock import patch, mock_open, MagicMock, Mock


def test_search_object():
    class TestSearch(search_objects.SearchObject):
        required = False
        required_trails = False

        def search(self, matched_filter_output, raw_data, config):
            return self.arguments["test"]
    searcher = TestSearch(test=True)
    assert searcher.search(None, None, None)


def test_conf_file_read():
    data = "[General]\nTestValue = 132"
    with patch("builtins.open", mock_open(read_data=data)) as mock_file:
        mock_file.is_file = MagicMock(return_value=True)
        configuration = conf.generate_event_search_config(file_input=mock_file)
        assert configuration['General']['TestValue'] == '132'


def test_remove_indices():
    configuration = conf.generate_event_search_config()
    ignore_indices = [[1], [3]]
    start_IPP = [1, 5, 9]
    end_IPP = [3, 6, 11]
    mets_found = 2
    test1, test2 = [5, 9], [6, 11]
    result1, result2 = event_search.remove_indices(
        ignore_indices,
        mets_found,
        start_IPP,
        end_IPP,
        configuration
    )
    assert test1 == result1
    assert test2 == result2


def test_gaussian_noise():
    reals = np.zeros([1, 10, 10], dtype=np.float64)
    imags = np.ones([1, 10, 10], dtype=np.float64)
    test_data = reals + imags * 1j
    test_axis = 2
    gauss_calc = calc_noise.CalculateGaussianNoise()
    return_value = gauss_calc.calc(test_data, test_axis)
    assert return_value["mean"] == 0.5
    assert return_value["std_dev"] == 0.5
    assert isclose(return_value["confidence_interval"][0], 0.65, abs_tol=10**-2)
    assert isclose(return_value["confidence_interval"][1], 0.39, abs_tol=10**-2)


def test_partial_data_input():
    test_data = raw_data.RawDataInterface(None, load_on_init=False)
    test_data.data = np.zeros([1, 30, 30], dtype=np.complex128)
    test_data.data[:, :test_data.data.size // 2:2, :] = 1
    test_data.axis['channel'] = 0
    test_data.axis['sample'] = 1
    test_data.axis['pulse'] = 2
    test_data.path = "test"
    test_best_peak = np.zeros(5, dtype=np.complex128)
    test_best_doppler = np.zeros(5, dtype=np.int32)
    test_best_start = np.zeros(5, dtype=np.int32)
    test_filter_output = {
        'max_pow_per_delay': np.ones([56, 5], dtype=np.complex128),
        'best_doppler': test_best_doppler,
        'best_peak': test_best_peak,
        'best_start': test_best_start,
        'pulse_length': 5
    }
    configuration = conf.generate_event_search_config()
    configuration["General"]["MOVE_STD_WINDOW"] = "2"
    configuration["General"]["least_ipp_available"] = "3"
    configuration["General"]["start_std_coherr_percent"] = "3"
    configuration["General"]["CRITERIA_N"] = "1"
    configuration["General"]["min_range_separation_split"] = "1e-02"
    configuration["General"]["xcorr_noise_limit"] = "0.05"

    signal = signal_model.barker_code_13(test_data.data.shape[1], 2)

    class TestSearch(search_objects.SearchObject):
        required = False
        required_trails = True

        def search(self, matched_filter_output, raw_data, config):
            if (matched_filter_output["max_pow_per_delay"].shape == (56, 30)
                    and matched_filter_output["pulse_length"] == 30):
                return np.ones(30, dtype=bool)
            return np.zeros(30, dtype=bool)
    searcher = TestSearch()
    result = event_search.search(test_data, configuration, test_filter_output,
                                 signal, search_function_objects=[searcher])
    assert np.all(result[0])


"""
Kan bara smoke-testas innan refakturering
def test_event_search_functionality():
    result = np.zeros(100, dtype=bool)
    configuration = conf.generate_event_search_config()

    class TestSearch(search_objects.SearchObject):
        required = False
        required_trails = False

        def search(self, matched_filter_output, raw_data, config):
            return np.zeros(self.arguments["length"], dtype=bool)
    searcher = TestSearch(length=100)
    assert np.array_equal(event_search.search(None, configuration, {}, None,
                                              search_function_objects=[searcher]), [result])
"""


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
    assert configuration['General']['least_ipp_available'] is not None
    assert configuration['General']['min_ipp_separation_split'] is not None
    assert configuration['General']['min_dop_separation_split'] is not None
    assert configuration['General']['min_range_separation_split'] is not None
    assert configuration['General']['smoothing_window'] is not None
    assert configuration['General']['IPP_extend'] is not None
    assert configuration['General']['allow_analysis_overlap'] is not None
    assert configuration['General']['event_max_overlap'] is not None
