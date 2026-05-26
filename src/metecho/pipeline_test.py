from pathlib import Path
from typing import Optional

from hardtarget import direction_of_arrival, target_estimation
from pyant.models import Array, ArrayParams  # ,InterpolatedArray, InterpolatedArrayParams
from radardef.components import RadarStation
from radardef.radar_stations import Mu

from metecho.events import event_search
from metecho.tools.mpi_decorators import get_mpi

config = Path("../hardtarget/docs/examples/cfg/test.ini")


def pipeline(
    path: Path,
    station=RadarStation,
    config: Optional[Path] = None,
    output: Optional[Path] = None,
):
    comm = get_mpi()

    # If needed convert the data
    # TODO

    # Load the data
    if comm.rank == 0:
        data = station.load_data(path)
        assert data is not None
    else:
        data = None
    data = comm.bcast(data, root=0)

    # Start an event search first
    events, echo = event_search(
        data,
        config=None,
        progress=True,
        output=output,
        comm=comm,
    )

    # Analyse events
    # No point in parallel process one event, better to allocate one process per event
    meteors = events.meteors[comm.rank : len(events.meteors) : comm.size]
    for meteor in meteors:
        # Event location
        start_time = events.event_search_start_us + meteor.start_ipp * data.experiment.t_ipp_usec
        end_time = events.event_search_start_us + meteor.end_ipp * data.experiment.t_ipp_usec

        # Target estimation
        target_estimation(
            data,
            config=config,
            start_time=start_time,
            end_time=end_time,
            output=Path(output) / "target_estimation" if output else None,
        )

        if isinstance(station.beam, Array) and isinstance(station.beam_parameters, ArrayParams):
            direction_of_arrival(
                data,
                config=config,
                start_time=start_time,
                end_time=end_time,
                output=Path(output) / "direction_of_arrival" if output else None,
                array_beam=station.beam,
                beam_params=station.beam_parameters,
            )


import time

start = time.time()
pipeline(
    path=Path("/home/hampusa/Documents/Data/MU/MUI20140524_CONV/20140524/test_batch/"),
    config=config,
    station=Mu(),
    output=Path("results"),
)
print(f"Total time: {time.time() - start}, analysed time: 277s ")
