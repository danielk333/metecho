import numpy as np
from metecho.event_search import base
from metecho.event_search import conf
from unittest.mock import patch, mock_open, MagicMock


def test_conf_file_read():
    data = "[General]\nTestValue = 132"
    with patch("builtins.open", mock_open(read_data=data)) as mock_file:
        mock_file.is_file = MagicMock(return_value=True)
        configuration = conf.generate_event_search_config(file_input=mock_file)
        assert configuration['General']['TestValue'] == '132'


def test_base_functionality():
    test_value = np.zeros(100, dtype=np.complex128)
    result = np.zeros(100, dtype=bool)
    configuration = conf.generate_event_search_config()
    assert np.array_equal(base.search(test_value, configuration, None, None), result)


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
