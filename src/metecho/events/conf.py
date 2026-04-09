import configparser
from pathlib import Path
from typing import Any, Optional

from radardef.types.types import ExpDef
from scipy.constants import c

from metecho.events.types import EventSearchConfig


def generate_default_event_search_config(exp_def: ExpDef) -> EventSearchConfig:

    rx_start_samp = exp_def.t_rx_start_usec / exp_def.t_samp_usec
    rx_end_samp = exp_def.t_rx_end_usec / exp_def.t_samp_usec
    tx_start_samp = exp_def.t_tx_start_usec / exp_def.t_samp_usec
    tx_end_samp = exp_def.t_tx_end_usec / exp_def.t_samp_usec

    rx_samps = rx_end_samp - rx_start_samp
    tx_samps = tx_end_samp - tx_start_samp

    return EventSearchConfig(
        CRITERIA_N=3,
        MOVE_STD_WINDOW=10,
        FIND_CRITERIA_xcorr_sigma=1,
        FIND_CRITERIA_totpow_sigma=1.5,
        FIND_CRITERIA_dop_STD_sigma=0.5,
        FIND_CRITERIA_start_STD_sigma=0.5,
        dop_std_coherr=7e3,
        start_std_coherr=13,
        start_std_coherr_percent=0.7,
        dop_std_coherr_percent=0.6,
        pow_std_est=3,
        pow_std_filt=2,
        FIND_CRITERIA_dop_sigma=3,
        FIND_CRITERIA_ind_pm=3,
        min_dop_allowed=1e3 * exp_def.radar_frequency * 1e6 / c,
        max_start_allowed=int(rx_samps - tx_samps / 2),
        min_start_allowed=0,
        least_ipp_available=5,
        min_ipp_separation_split=20,
        min_dop_separation_split=10 * 1e3 * exp_def.radar_frequency * 1e6 / c,
        min_range_separation_split=4.0,
        smoothing_window=5,
        polyorder=2,
        IPP_extend=10,
        allow_analysis_overlap=3,
        event_max_overlap=5,
        dop_min_freq=-30000,
        dop_max_freq=5000,
        dop_step_size=1000,
        xcorr_noise_limit=0.5,
    )


def generate_event_search_config(
    file_input: Optional[str | Path] = None, exp_def: Optional[ExpDef] = None
) -> EventSearchConfig | None:

    if file_input:
        if isinstance(file_input, str):
            file_input = Path(file_input)

        if file_input is not None and file_input.is_file():
            config_parser = configparser.ConfigParser()
            config_parser.read([file_input])

            config: dict[str, Any] = {}
            for key, type in EventSearchConfig.__annotiations__:  # type: ignore[attr-defined]
                # Convert values to specific types
                if isinstance(type, int):
                    config[key] = config_parser.getint("GENERAL", key)
                elif isinstance(type, bool):
                    config[key] = config_parser.getboolean("GENERAL", key)
                elif isinstance(type, float):
                    config[key] = config_parser.getfloat("GENERAL", key)
                else:
                    # string
                    config[key] = config_parser.get("GENERAL", key).strip("'").strip('"')

            return EventSearchConfig(**config)

        return None
    elif exp_def:
        return generate_default_event_search_config(exp_def)

    return None
