import configparser

DEFAULT_CONFIG = {
    'General': {

        # Detection metrics
        'CRITERIA_N': '3',
        'MOVE_STD_WINDOW': '10',

        # Power and correlation limits
        'FIND_CRITERIA_xcorr_sigma': '1',
        'FIND_CRITERIA_totpow_sigma': '1.5',

        # Normal move STD
        'FIND_CRITERIA_dop_STD_sigma': '0.5',
        'FIND_CRITERIA_start_STD_sigma': '0.5',

        # Constant echo prescense search
        'dop_std_coherr': '7e3',
        'start_std_coherr': '13',
        'start_std_coherr_percent': '0.7',
        'dop_std_coherr_percent': '0.6',

        # Filtering parameters
        'pow_std_est': '3',
        'pow_std_filt': '2',

        # If echoes are present
        'FIND_CRITERIA_dop_sigma': '3',
        'FIND_CRITERIA_ind_pm': '3',

        # 0 dop removal
        # 1e3 * 1 * 46.5e6 / 299792458
        'min_dop_allowed': '310.21460853428140610528634446167421596710081345675480601983656306',
        # 85 - 26 / 2
        'max_start_allowed': '72',
        'min_start_allowed': '0',

        # Recursive "index-island" detector
        'least_ipp_available': '5',
        'min_ipp_separation_split': '20',
        # 10e3 * 1 * 46.5e6 / 299792458
        'min_dop_separation_split': '1551.0730426714070305264317223083710798355040672837740300991828153',
        'min_range_separation_split': '4.0',

        'smoothing_window': '5',
        'polyorder': '2',

        'IPP_extend': '10',

        # Sequential analysis config
        'allow_analysis_overlap': '3',
        'event_max_overlap': '5',

        # Xcorr settings
        'dop_min_freq': '-30000',
        'dop_max_freq': '5000',
        'dop_step_size': '1000',

        # Noise limit
        'xcorr_noise_limit': '0.5',

        # Plot coloring
        'match_found': 'magenta',
        'match_not_found': 'blue',
    }
}


def generate_event_search_config(file_input=None):
    config = configparser.ConfigParser()
    config.read_dict(DEFAULT_CONFIG)

    if file_input is not None and file_input.is_file():
        config.read([file_input])

    return config
