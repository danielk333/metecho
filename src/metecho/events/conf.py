from pathlib import Path

from hardtarget.echo_search.types import EchoSearchCfgParams
from hardtarget.process.configuration import extract_config_from_dict, extract_config_section
from radardef.types.types import ExpDef
from scipy.constants import c

from metecho.events.types import EventCriteriaCfg, EventSearchCfg, EventSelectCfg


def extract_event_search_configurations(
    config: dict | Path,
) -> tuple[EventSearchCfg, EventCriteriaCfg, EventSelectCfg, EchoSearchCfgParams]:
    if isinstance(config, Path):
        event_search_cfg = EventSearchCfg(
            **extract_config_section(config, section="event_search", cfg_type=EventSearchCfg)
        )
        event_criteria_cfg = EventCriteriaCfg(
            **extract_config_section(config, section="event_criterias", cfg_type=EventCriteriaCfg)
        )
        event_select_cfg = EventSelectCfg(
            **extract_config_section(config, section="event_select", cfg_type=EventSelectCfg)
        )
        echo_search_cfg = EchoSearchCfgParams(
            **extract_config_section(config, section=None, cfg_type=EchoSearchCfgParams)
        )
    else:
        event_search_cfg = extract_config_from_dict(config, EventSearchCfg)
        event_criteria_cfg = extract_config_from_dict(config, EventCriteriaCfg)
        event_select_cfg = extract_config_from_dict(config, EventSelectCfg)
        echo_search_cfg = extract_config_from_dict(config, EchoSearchCfgParams)

    return event_search_cfg, event_criteria_cfg, event_select_cfg, echo_search_cfg


def generate_default_configurations(exp_def: ExpDef):

    rx_start_samp = exp_def.t_rx_start_usec / exp_def.t_samp_usec
    rx_end_samp = exp_def.t_rx_end_usec / exp_def.t_samp_usec
    tx_start_samp = exp_def.t_tx_start_usec / exp_def.t_samp_usec
    tx_end_samp = exp_def.t_tx_end_usec / exp_def.t_samp_usec

    rx_samps = rx_end_samp - rx_start_samp
    tx_samps = tx_end_samp - tx_start_samp

    event_search_cfg = EventSearchCfg(
        dop_std_coherr=7e3,
        start_std_coherr=13,
        pow_std_est=3,
        pow_std_filt=2,
        allow_analysis_overlap=3,
        corr_filter_limit=0.5,
        noise_time_window_sec=1,
        move_std_window=10,
        noise_chunk_size=100,
    )

    event_criteria_cfg = EventCriteriaCfg(
        criteria_n=3,
        correlation_sigma=1,
        totpow_sigma=1.5,
        doppler_std_sigma=0.5,
        start_std_sigma=0.5,
        doppler_sigma=3,
        ind_pm=3,
        min_start_allowed=tx_start_samp,
        max_start_allowed=int(rx_samps - tx_samps / 2),
        min_dop_allowed=1e3 * exp_def.radar_frequency * 1e6 / c,
        start_std_coherr_percent=0.7,
        dop_std_coherr_percent=0.6,
    )

    event_select_cfg = EventSelectCfg(
        least_ipp_available=5,
        min_ipp_separation_split=20,
        min_dop_separation_split=10 * 1e3 * exp_def.radar_frequency * 1e6 / c,
        min_range_separation_split=4,
        ipp_extend=10,
        smoothing_window=5,
        polyorder=2,
        event_max_overlap=10,
    )

    echo_search_cfg = EchoSearchCfgParams(
        n_ipp=1,
        min_range_gate=0,
        max_range_gate=-1,
        range_gate_step=int(exp_def.baud_length_usec / (exp_def.t_samp_usec * 2)),
        doppler_freq_min=-25000,
        doppler_freq_max=25000,
        doppler_freq_step=1000,
        corr_filter_limit=event_search_cfg.corr_filter_limit,
    )

    return event_search_cfg, event_criteria_cfg, event_select_cfg, echo_search_cfg
