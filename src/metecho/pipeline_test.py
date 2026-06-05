from pathlib import Path
from typing import Optional

import numpy as np
from hardtarget import direction_of_arrival, target_estimation
from pyant.models import Array, ArrayParams  # ,InterpolatedArray, InterpolatedArrayParams
from radardef import RadarStation
from radardef.components import DataLoader
from radardef.radar_stations import Mu
from radardef.tools.mpi_tools import MPIProgress

# from tqdm import tqdm
from metecho.events import event_search
from metecho.events.types import Event
from metecho.tools.mpi_decorators import CommMock, CommObject, get_mpi

config = Path("../hardtarget/docs/examples/cfg/test.ini")


def analyse_event(
    data: DataLoader,
    event: Event,
    config: Path,
    station: RadarStation,
    output: Optional[Path | str] = None,
    progress: bool | MPIProgress = False,
):
    if progress:
        prog = MPIProgress(
            tot=2,
            desc="Event proccessing",
            parent_progress=progress if isinstance(progress, MPIProgress) else None,
            transient=True,
        )
    else:
        prog = False

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
        progress=progress,
    )

    if prog:
        prog.update(1)

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
            progress=progress,
        )

    if prog:
        prog.update(1)


def proccess_dir(
    path: Path,
    station: RadarStation,
    output: Path,
    config: Path,
    comm: CommObject = CommMock(),
    progress: bool = False,
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
        progress=progress,
        output=output,
        comm=comm,
    )

    comm.barrier()

    # Analyse detected meteors and trails

    events = events.meteors + events.trails
    tot_events = len(events)
    events = events[comm.rank : len(events) : comm.size]
    if progress:
        prog = MPIProgress(tot=tot_events, desc="Analysing events")
    else:
        prog = False

    for event in events:
        analyse_event(
            data=data,
            event=event,
            config=config,
            station=station,
            output=output,
            progress=prog
            if comm.size == 1
            else False,  # If processing events on several processes there will too many bars
        )

        if prog:
            prog.update(1)

    comm.barrier()


def pipeline(
    path: Path,
    station: RadarStation,
    output: Path,
    config: Path,
    progress: bool = False,
):
    comm = get_mpi()

    if not station.is_data_compatible(path):
        target_format = station.converters.available_target_formats(station.validator.format)[0]
        conv_path = station.convert(path, target_format, dst=output, progress=progress)
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
        proccess_dir(path, station, output, config, comm, progress=progress)


pipeline(
    # path=Path("/home/hampusa/Documents/Data/MU/MUI20140524_CONV/20140524/test_batch/"),
    path=Path("../tmp_data/mui_object/2019-11-06/04-00-00"),
    # path=Path("../tmp_data/mui_larger_batch"),
    config=config,
    station=Mu(),
    output=Path("results"),
    progress=True,
)
