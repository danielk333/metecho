import datetime as dt
import tempfile
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest
from hardtarget.data_simulation.simulate_h5 import simulate_h5
from hardtarget.echo_search.types import EchoSearchOutArgs
from radardef.radar_def import RadarDef
from radardef.radar_stations import Mu
from radardef.radar_stations.mu.experiments import mu_exp

from metecho.events.event_search import calculate_noise, echo_post_process, event_search
from metecho.events.types import EventSearchCfg
from metecho.plot.event_search import plot_events


def test_echo_post_process():
    """TODO: Needs to be improved"""

    exp_def = mu_exp
    analysis = EchoSearchOutArgs(
        epoch_us=1791204526000000,
        t=np.arange(0, 4 * exp_def.t_ipp_usec, exp_def.t_ipp_usec) * 1e-6,
        max_corr=np.array([10.0, 10.0, 2.0, 2.0]),
        max_corr_ind=np.array([10.0, 10.0, 11.0, 11.0]),
        max_corr_delay=np.array([10.0, 10.0, 11.0, 11.0]),
        best_doppler=np.array([1.0, 1.0, 2.0, 2.0]),
        tot_pow=np.array([10.0, 11.0, 1.0, 2.0]),
        mean=np.zeros((4, 1)),
        std_dev=np.zeros((4, 1)),
    )

    config = EventSearchCfg(
        move_std_window=2,
        dop_std_coherr=10.0,
        start_std_coherr=10.0,
        corr_filter_limit=5.0,
        pow_std_est=1.0,
        noise_chunk_size=5,
    )

    result = echo_post_process(analysis, exp_def, config)

    np.testing.assert_array_equal(result.tot_pow, analysis.tot_pow)
    np.testing.assert_array_equal(result.max_corr, analysis.max_corr)
    np.testing.assert_array_equal(result.best_doppler, analysis.best_doppler)
    np.testing.assert_array_equal(result.epoch_us, analysis.epoch_us)

    assert len(result.doppler_std) == len(analysis.best_doppler)
    assert len(result.start_std) == len(analysis.max_corr_ind)

    assert len(result.tot_pow_filt) > 0
    np.testing.assert_array_equal(
        result.best_peak_filt,
        analysis.max_corr[np.isin(analysis.tot_pow, result.tot_pow_filt)],
    )
    assert result.exp_def is exp_def


def test_calculate_noise():

    mean = np.array(
        [
            -2.11745481e-03,
            -1.03865871e-03,
            -8.31625491e-04,
            -4.44455151e-04,
            9.96870122e-04,
            -6.73965236e-04,
            -3.51584384e-03,
            2.11938989e-03,
            -2.68596645e-03,
            8.06089516e-04,
            -2.71811580e-03,
            -3.79494258e-03,
            2.19567801e-03,
            6.85756676e-05,
            -2.82926197e-03,
            -1.85972643e-03,
            1.03762676e-03,
            2.94422870e-03,
            1.23907985e-03,
            -2.14327395e-03,
        ]
    )
    std_dev = np.array(
        [
            0.05994221,
            0.06018704,
            0.06320756,
            0.06318842,
            0.0642245,
            0.0671224,
            0.06453224,
            0.05997078,
            0.05781478,
            0.05907375,
            0.06171208,
            0.06551381,
            0.06551403,
            0.06229473,
            0.06117271,
            0.06267051,
            0.05946621,
            0.05788014,
            0.05891441,
            0.05879873,
        ]
    )

    gaussian_chunks = calculate_noise(mean=mean, std_dev=std_dev, epoch_us=1000, exp_def=mu_exp, chunk_size=5)
    np.testing.assert_array_almost_equal(
        gaussian_chunks.mean, np.array([-0.00068706, -0.00079006, -0.00141561, 0.00024359])
    )
    np.testing.assert_array_almost_equal(
        gaussian_chunks.std_dev, np.array([0.06218262, 0.06183952, 0.06330855, 0.05960062])
    )
    assert gaussian_chunks.epoch_us == 1000
    assert gaussian_chunks.chunk_size_usec == 5 * mu_exp.t_ipp_usec


@pytest.mark.skip(reason="Work in progress")
def test_meteor_search():
    # TODO
    pass


@pytest.mark.skip(reason="Work in progress")
def test_create_event_cluster():
    # TODO
    pass


def test_event_search(plot):

    exp_def = mu_exp

    # ## Define a objects trajectory function,
    # ---
    r0: float = 110e3
    v0: float = 50e3
    a0: float = -0.05e3
    # Initial position over radar
    k0 = np.array([0, 0, 1])
    v_vec = np.array([0, 0, -1])

    def trajectory_func(t: npt.NDArray) -> tuple[npt.NDArray, npt.NDArray]:
        # 3d position
        x_start = k0 * r0
        # Velocity vector
        distance_traveled = v0 * t + a0 * 0.5 * t**2

        trajectory = x_start[:, None] + v_vec[:, None] * distance_traveled[None, :]
        r = np.linalg.norm(trajectory, axis=0)
        two_way_range = 2 * r
        rx_k_vecs = trajectory / r

        # trajectory
        return two_way_range, rx_k_vecs

    with tempfile.TemporaryDirectory() as temp_dir:
        # ## Simulate the experiment with the MU radars beam.
        output_path = Path(temp_dir) / "sim"
        station = Mu()
        target_start_ipp = 35
        target_end_ipp = 67
        measurement_length_us = exp_def.t_ipp_usec * 100
        target_start_time_us = exp_def.t_ipp_usec * target_start_ipp
        target_end_time_us = exp_def.t_ipp_usec * target_end_ipp
        start = dt.datetime.now(tz=dt.timezone.utc)
        sim_data = simulate_h5(
            output_dir=output_path,
            exp_def=exp_def,
            start_time=start,
            end_time=start + dt.timedelta(microseconds=measurement_length_us),
            target_start_time=target_start_time_us,
            target_end_time=target_end_time_us,
            target_relative_time=True,
            trajectory_function=trajectory_func,
            noise_sigma=0.5,
            beam=station.beam,
            beam_params=station.beam_parameters,
        )

        # Search the data for events, we expect one event to be found
        events, echo, noise = event_search(
            data=sim_data,
            config=None,  # Default configuration generation
            exp_def=exp_def,
            # output=Path(temp_dir) / "event_search",
        )

        if plot:
            data = RadarDef().load_data(sim_data)
            plot_events(echo, events, data, log=True)

        assert len(events.meteors) == 1, f"Expected 1 found meteor, found: {len(events.meteors)}"
        meteor = events.meteors[0]
        assert (meteor.event_indices == events.meteor_indicies).all(), (
            "Total indicies does not match the meteor indicies"
        )
        assert np.logical_and(
            meteor.event_indices >= target_start_ipp, meteor.event_indices <= target_end_ipp
        ).all(), "Event indicies marks events outside of the expected window"
