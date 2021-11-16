import numpy as np
from metecho.event_search import base
from metecho.event_search import config


def test_base_functionality():
    test_value = np.zeros(100, dtype=np.complex128)
    result = np.zeros(100, dtype=bool)
    assert np.array_equal(base.search(test_value, test_value, test_value, test_value, test_value), result)


def test_get_config():
    conf = config.generate_event_search_config()
    assert hasattr(conf, 'CRITERIA_N')
    assert hasattr(conf, 'MOVE_STD_WINDOW')
    assert hasattr(conf, 'FIND_CRITERIA_xcorr_sigma')
    assert hasattr(conf, 'FIND_CRITERIA_totpow_sigma')
    assert hasattr(conf, 'FIND_CRITERIA_dop_STD_sigma')
    assert hasattr(conf, 'FIND_CRITERIA_start_STD_sigma')
    assert hasattr(conf, 'dop_std_coherr')
    assert hasattr(conf, 'start_std_coherr')
    assert hasattr(conf, 'start_std_coherr_percent')
    assert hasattr(conf, 'dop_std_coherr_percent')
    assert hasattr(conf, 'pow_std_est')
    assert hasattr(conf, 'pow_std_filt')
    assert hasattr(conf, 'FIND_CRITERIA_dop_sigma')
    assert hasattr(conf, 'FIND_CRITERIA_ind_pm')
    assert hasattr(conf, 'min_dop_allowed')
    assert hasattr(conf, 'max_start_allowed')
    assert hasattr(conf, 'min_start_allowed')
    assert hasattr(conf, 'least_ipp_avalible')
    assert hasattr(conf, 'min_ipp_separation_split')
    assert hasattr(conf, 'min_dop_separation_split')
    assert hasattr(conf, 'min_range_separation_split')
    assert hasattr(conf, 'smoothing_window')
    assert hasattr(conf, 'IPP_extend')
    assert hasattr(conf, 'allow_analysis_overlap')
    assert hasattr(conf, 'event_max_overlap')

