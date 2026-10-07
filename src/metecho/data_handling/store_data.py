import datetime as dt
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, ClassVar, NamedTuple, Protocol, Union

import h5py
import numpy as np

from metecho.events.types import Events
from metecho.noise.types import GaussianNoiseChunks

try:
    # Only available from python 3.12
    from types import get_original_bases  # type: ignore[attr-defined,unused-ignore]

    def orig_bases(cls: type) -> tuple[Any, ...]:
        """Get bases of class"""
        return get_original_bases(cls)

except ImportError:

    def orig_bases(cls: type) -> tuple[Any, ...]:
        """Get bases of class"""
        return cls.__orig_bases__  # type: ignore[attr-defined]


def is_namedtuple(data_type: Any) -> bool:
    """Is object a NamedTuple"""

    try:
        return orig_bases(data_type) == (NamedTuple,)
    except TypeError:
        return False


class IsDataclass(Protocol):
    """Is Dataclass protocol"""

    __dataclass_fields__: ClassVar[dict[str, Any]]
    __annotations__: dict[str, Any]


def store_noise(gaussian_noise: GaussianNoiseChunks, path: Path) -> None:
    """
    Store gaussian noise according to naming convention at given path.
    """

    _dt = dt.datetime.fromtimestamp(gaussian_noise.epoch_us * 1e-6, dt.timezone.utc)
    time_string = _dt.strftime("%Y-%m-%dT%H-%M-%S")
    folder_name = f"{time_string[0:10]}/{time_string[11:13]}-00-00/noise"
    file_name = f"noise-{time_string}.h5"

    path = path / folder_name / file_name
    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)
    with h5py.File(path, "w") as file:
        store_params(file, gaussian_noise)


def store_events(events: Events, path: Path) -> None:
    """
    Store events according to naming convention at given path.
    """
    _dt = dt.datetime.fromtimestamp(events.event_search_start_us * 1e-6, dt.timezone.utc)
    time_string = _dt.strftime("%Y-%m-%dT%H-%M-%S")
    folder_name = f"{time_string[0:10]}/{time_string[11:13]}-00-00/events"
    file_name = f"events-{time_string}.h5"

    path = path / folder_name / file_name
    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)
    with h5py.File(path, "w") as file:
        store_params(file, events)


def store_params(group: h5py.Group | h5py.File, object: Union[NamedTuple, IsDataclass]) -> None:
    """
    Store a dataclass or NamedTuple in group.
    H5 file will get same structure as object.

    Args:
        group: h5py group to write to.
        object: Data to store.
    """

    if is_namedtuple(type(object)):
        key_data_pairs = object._asdict()  # type: ignore[union-attr]
    elif is_dataclass(object):
        key_data_pairs = asdict(object)

    for key, data in key_data_pairs.items():
        if data is not None:
            if isinstance(data, Path):
                data = str(data)
            elif isinstance(data, np.datetime64):
                data = str(np.datetime_as_string(data))
            elif isinstance(data, dict):
                data = str(data)
            elif is_namedtuple(type(data)) or is_dataclass(data):
                sub_group = group.create_group(key)
                store_params(sub_group, data)
                continue
            elif (
                isinstance(data, (list, tuple))
                and len(data) > 0
                and (is_dataclass(data[0]) or is_namedtuple(type(data[0])))
            ):
                list_group = group.create_group(key)

                for i, data_point in enumerate(data):
                    if is_dataclass(data_point) or is_namedtuple(type(data_point)):
                        list_key = key + f"_{i}"
                        sub_group = list_group.create_group(list_key)
                        store_params(sub_group, data_point)
                continue

            group.create_dataset(key, data=data)
