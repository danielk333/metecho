import numpy as np
from metecho.data import raw_data
from metecho.event_search import event_search, conf, search_objects
from metecho.generalized_matched_filter import signal_model
from unittest.mock import patch, mock_open, MagicMock, Mock


def test_search_object():
    class TestSearch(search_objects.SearchObject):
        def search(self, matched_filter_output):
            return self.arguments["test"]
    searcher = TestSearch(test=True)
    assert searcher.search(None)


def test_conf_file_read():
    data = "[General]\nTestValue = 132"
    with patch("builtins.open", mock_open(read_data=data)) as mock_file:
        mock_file.is_file = MagicMock(return_value=True)
        configuration = conf.generate_event_search_config(file_input=mock_file)
        assert configuration['General']['TestValue'] == '132'


def test_partial_data_input():
    test_data = raw_data.RawDataInterface(None, load_on_init=False)
    test_data.data = np.ones([1, 10, 10], dtype=np.complex128)
    test_data.axis['channels'] = 0
    test_data.axis['samples'] = 1
    test_data.axis['pulses'] = 2
    test_filter_output = {
        'powmaxall': np.ones([36, 5], dtype=np.complex128),
        'sample_length': 10,
        'pulse_length': 5
    }
    configuration = conf.generate_event_search_config()

    class TestSearch(search_objects.SearchObject):
        def search(self, matched_filter_output):
            if (matched_filter_output["powmaxall"].shape == (36, 10)
                and matched_filter_output["sample_length"] == 10
                and matched_filter_output["pulse_length"] == 10):
                return True
            return False
    searcher = TestSearch()
    result = event_search.search(test_data, configuration, test_filter_output, [searcher])
    assert result[0]


def test_event_search_functionality():
    result = np.zeros(100, dtype=bool)

    class TestSearch(search_objects.SearchObject):
        def search(self, matched_filter_output):
            return np.zeros(self.arguments["length"], dtype=bool)
    searcher = TestSearch(length=100)
    assert np.array_equal(event_search.search(None, None, None, [searcher]), [result])


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
