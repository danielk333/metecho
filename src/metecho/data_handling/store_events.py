import datetime as dt
from dataclasses import asdict, is_dataclass
from pathlib import Path
from types import get_original_bases
from typing import Any, ClassVar, NamedTuple, Protocol

import h5py
import numpy as np

from metecho.events.types import Events


def is_namedtuple(data_type: Any) -> bool:
    # TODO: Accept and isntance of a object aswell and not just the type

    try:
        return get_original_bases(data_type) == (NamedTuple,)
    except TypeError:
        return False


class IsDataclass(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Any]]
    __annotations__: dict[str, Any]


def store_events(events: Events, path: Path) -> None:
    """
    file name format..... TBD

    """
    if not path.is_dir():
        path.mkdir(parents=True)
    _dt = dt.datetime.fromtimestamp(events.event_search_start_us * 1e-6, dt.timezone.utc)
    time_string = _dt.strftime("%Y-%m-%dT%H-%M-%S")
    file_name = f"events-{time_string}.h5"
    with h5py.File(path / file_name, "w") as file:
        store_params(file, events)


def store_params(group: h5py.Group | h5py.File, object: NamedTuple | IsDataclass) -> None:

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
            elif (isinstance(data, list) or isinstance(data, tuple)) and len(data) > 0:
                if is_dataclass(data[0]) or is_namedtuple(type(data[0])):
                    list_group = group.create_group(key)

                    for i, data_point in enumerate(data):
                        if is_dataclass(data_point) or is_namedtuple(type(data_point)):
                            list_key = key + f"_{i}"
                            sub_group = list_group.create_group(list_key)
                            store_params(sub_group, data_point)
                    continue
                else:
                    data = data

            group.create_dataset(key, data=data)
