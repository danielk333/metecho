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
        prog.close()


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
    events, echo, noise = event_search(
        data,
        config=None,
        progress=progress,
        output=output,
        comm=comm,
    )

    # Analyse detected meteors and trails

    events = events.meteors + events.trails
    tot_events = len(events)
    events = events[comm.rank : len(events) : comm.size]
    if progress:
        prog = MPIProgress(tot=tot_events, desc="Analysing events")
        if get_mpi().size > 2:
            n_processes_prog = MPIProgress(
                tot=get_mpi().size,
                desc="Finished ",
                parent_progress=prog,
                transient=True,
            )
        else:
            n_processes_prog = False
    else:
        prog = False
        n_processes_prog = False

    for event in events:
        # Note that when analysing events the same dataloader is shared between all processes,
        # Each process has different lists of objects to analyse, where each object is one big step away from another
        # meaning tha the cache function is not being utilized properly.

        # Thought: Should the events be sorted acoording to time and then split into comm.size chunks where each chunk gets its own dataloader
        #          Will this lead to comm.size * cache RAM usage?
        # Thoght 2: Should the events be sorted according to time and then spit the same way as they are today? How to utilize the processes
        #           that are finished before the others? Send events to be utilized there?

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

    if n_processes_prog:
        n_processes_prog.update(1)
        n_processes_prog.close()

    comm.barrier()
    if prog:
        prog.close()


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
    # path=Path("../tmp_data/mui_object/MUI.191106.042339"),  # Run without MPI
    # path=Path("../tmp_data/mui_larger_batch"),
    path=Path("/home/hampusa/Documents/Data/MU/2014-05-24/12-00-00/converted_data/").resolve(),
    config=config,
    station=Mu(),
    output=Path("results"),
    progress=True,
)
