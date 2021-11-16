class Config():
    def __init__(self):
        # Detection metrics
        self.CRITERIA_N = 3
        self.MOVE_STD_WINDOW = 10

        # Power and correlation limits
        self.FIND_CRITERIA_xcorr_sigma = 1
        self.FIND_CRITERIA_totpow_sigma = 1.5

        # Normal move STD
        self.FIND_CRITERIA_dop_STD_sigma = 0.5
        self.FIND_CRITERIA_start_STD_sigma = 0.5

        # Constant echo prescense search
        self.dop_std_coherr = 7e3
        self.start_std_coherr = 13
        self.start_std_coherr_percent = 0.7
        self.dop_std_coherr_percent = 0.6

        # Filtering parameters
        self.pow_std_est = 3
        self.pow_std_filt = 2

        # If echoes are present
        self.FIND_CRITERIA_dop_sigma = 3
        self.FIND_CRITERIA_ind_pm = 3

        # 0 dop removal
        self.min_dop_allowed = 1e3 * (2 * 46.5e6) / 299792458
        self.max_start_allowed = 85 - 26 / 2
        self.min_start_allowed = 0

        # Recursive "index-island" detector
        self.least_ipp_avalible = 5
        self.min_ipp_separation_split = 20
        self.min_dop_separation_split = (10e3 * 2 * 46.5e6) / 299792458
        self.min_range_separation_split = 4.0

        self.smoothing_window = 4

        self.IPP_extend = 10

        # Sequential analysis config
        self.allow_analysis_overlap = 3
        self.event_max_overlap = 5


def generate_event_search_config():
    return Config()
