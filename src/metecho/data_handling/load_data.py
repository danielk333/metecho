import datetime as dt
import inspect
import logging
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar, get_args, get_origin

import h5py
import numpy as np

from metecho.data_handling.store_data import is_namedtuple
from metecho.events.types import Events
from metecho.noise.types import GaussianNoiseChunks

logger = logging.getLogger(__name__)


def load_events(path: Path) -> Events:
    """Load events from file"""

    with h5py.File(path, "r") as file:
        events = load_object_from_group(file, Events)

    return events


def load_noise(path: Path) -> GaussianNoiseChunks:
    """Load gaussain noise from file"""
    with h5py.File(path, "r") as file:
        noise = load_object_from_group(file, GaussianNoiseChunks)

    return noise


def get_exact_annotations(data_type: Any) -> dict:
    """
    Returns a dictionary of fieldnames mapped to their exact types, works also with generic types.
    """

    base_class = get_origin(data_type)

    if base_class is None:
        return inspect.get_annotations(data_type)

    raw_annotations = inspect.get_annotations(base_class)
    type_map = dict(zip(base_class.__parameters__, get_args(data_type)))

    exact_annotations = {}
    for field_name, field_type in raw_annotations.items():
        if isinstance(field_type, TypeVar) and field_type in type_map:
            exact_annotations[field_name] = type_map[field_type]
        else:
            exact_annotations[field_name] = field_type

    return exact_annotations


GenericObject = TypeVar("GenericObject")


def load_object_from_group(group: h5py.Group, object_type: type[GenericObject]) -> GenericObject:
    """
    Load a dataclass or NamedTuple from group.
    Assumes h5 file is structured the same as the object type

    Args:
        group: h5py group to read from
        object_type: Class of object to read.
    Returns:
        Data of type object_type extracted from group.

    """

    # Dict containing the decoded data
    decoded_data = {}

    # Get Key and Type pairs from the given object
    annotations = get_exact_annotations(object_type)

    # If object is a dataclass only read datapoints that is a part of the init
    if is_dataclass(object_type):
        for field in fields(object_type):
            if not field.init:
                del annotations[field.name]

    # Extract each key from the h5 group
    for key, data_type in annotations.items():
        if key in group:
            h5_section = group[key]
        else:
            if type(None) not in data_type.__args__:
                logger.warning(f"No value present for key: {key}")

            data = None

        if isinstance(h5_section, h5py.Dataset):
            data = h5_section[()]
            if isinstance(data, bytes):
                data = data.decode()
            elif isinstance(data, np.ndarray) and data.size > 0 and isinstance(data[0], bytes):
                data = [d.decode() for d in data]

            if data_type == np.datetime64:
                data = np.datetime64(str(data))
            elif data_type == dt.datetime:
                data = dt.datetime.strptime(str(data), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=dt.timezone.utc)
            elif is_namedtuple(data_type) and isinstance(data, str):
                a = data.strip("{}")
                d = dict(item.split(": ") for item in a.split(", "))
                data = data_type(**d)
            elif data_type == dict and isinstance(data, str):
                a = data.strip("{}")
                data = dict(item.split(": ") for item in a.split(", "))
            elif data_type.__name__ == "list" and isinstance(data, np.ndarray) and data.size == 0:
                data = []
        else:
            if data_type.__name__ == "list":
                sub_type = data_type.__args__[0]
                if len(get_args(sub_type)) > 0:
                    base_type = get_origin(sub_type)
                    is_dataclass_or_named_tuple = is_dataclass(base_type) or is_namedtuple(base_type)
                else:
                    is_dataclass_or_named_tuple = is_dataclass(sub_type) or is_namedtuple(sub_type)
                sub_data = []
                for sub_key in h5_section:
                    # list of dataclass or named tuple
                    if is_dataclass_or_named_tuple:
                        sub_data.append(load_object_from_group(h5_section[sub_key], sub_type))
                    else:
                        sub_data.append(h5_section[sub_key])
                data = sub_data
            elif data_type.__name__ == "tuple":
                sub_types = list(data_type.__args__)
                sub_data = []
                for i, sub_key in enumerate(h5_section.keys()):
                    tuple_type = sub_types[i]
                    if is_dataclass(tuple_type) or is_namedtuple(tuple_type):
                        sub_data.append(load_object_from_group(h5_section[sub_key], tuple_type))
                    else:
                        sub_data.append(h5_section[sub_key])
                data = tuple(sub_data)

            else:
                # case of a Named tuple or dataclass
                data = load_object_from_group(h5_section, data_type)

        decoded_data[key] = data

    return object_type(**decoded_data)
