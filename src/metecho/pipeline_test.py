from pathlib import Path
from typing import Optional

import numpy as np
from hardtarget import direction_of_arrival, target_estimation
from pyant.models import Array, ArrayParams  # ,InterpolatedArray, InterpolatedArrayParams
from radardef import RadarStation
from radardef.components import DataLoader
from radardef.radar_stations import Mu

from metecho.events import event_search
from metecho.events.types import Event
from metecho.tools.mpi_decorators import CommMock, CommObject, get_mpi

config = Path("../hardtarget/docs/examples/cfg/test.ini")


def analyse_events(
    data: DataLoader,
    events: list[Event],
    config: Path,
    station: RadarStation,
    output: Optional[Path | str] = None,
    rank: int = 0,
    size: int = 1,
):
    events = events[rank : len(events) : size]
    for event in events:
        # Event location
        start_time = int(event.event_date.astype("datetime64[us]").astype("int"))
        end_time = start_time + (event.end_ipp - event.start_ipp) * data.experiment.t_ipp_usec

        sub_dir = f"{event.type}s/{event.type}_{np.datetime_as_string(event.event_date)}"

        target_estimation(
            data,
            config=config,
            start_time=start_time,
            end_time=end_time,
            output=output,
            sub_directory=sub_dir,
        )

        if isinstance(station.beam, Array) and isinstance(station.beam_parameters, ArrayParams):
            direction_of_arrival(
                data,
                config=config,
                start_time=start_time,
                end_time=end_time,
                output=output,
                sub_directory=sub_dir,
                array_beam=station.beam,
                beam_params=station.beam_parameters,
            )


def proccess_dir(
    path: Path,
    station: RadarStation,
    output: Path,
    config: Path,
    comm: CommObject = CommMock(),
):
    """
    Expected that conversion of data is done before running pipeline..?
    """

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

    # Analyse detected meteors and trails
    for e in [events.meteors, events.trails]:
        analyse_events(
            data=data,
            events=e,
            config=config,
            station=station,
            output=output,
            rank=comm.rank,
            size=comm.size,
        )

    comm.barrier()


def pipeline(
    path: Path,
    station: RadarStation,
    output: Path,
    config: Path,
):
    comm = get_mpi()

    if not station.is_data_compatible(path):
        target_format = station.converters.available_target_formats(station.validator.format)[0]
        conv_path = station.convert(path, target_format, dst=output, progress=True)
        if len(conv_path) > 0:
            path = conv_path[0]
        else:
            print("error no converted data")
            return

    comm.barrier()

    sub_dirs = [d for d in path.iterdir() if d.is_dir()]

    if sub_dirs:
        for dir in sub_dirs:
            proccess_dir(dir, station, output, config, comm)
    else:
        proccess_dir(path, station, output, config, comm)


import time

start = time.time()
pipeline(
    # path=Path("/home/hampusa/Documents/Data/MU/MUI20140524_CONV/20140524/test_batch/"),
    # path=Path("../tmp_data/mui_object/2019-11-06/04-00-00"),
    path=Path("../tmp_data/mui_larger_batch"),
    config=config,
    station=Mu(),
    output=Path("results"),
)
print(f"Total time: {time.time() - start}, analysed time: 277s ")
