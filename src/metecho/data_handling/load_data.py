import logging
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import TypeVar

import h5py
import numpy as np

from metecho.data_handling.store_data import is_namedtuple
from metecho.events.types import Events
from metecho.noise.types import GaussianNoiseChunks

logger = logging.getLogger(__name__)


def load_events(path: Path) -> Events:

    with h5py.File(path, "r") as file:
        events = load_object_from_group(file, Events)

    return events


def load_noise(path: Path) -> GaussianNoiseChunks:
    with h5py.File(path, "r") as file:
        noise = load_object_from_group(file, GaussianNoiseChunks)

    return noise


GenericObject = TypeVar("GenericObject")


def load_object_from_group(group: h5py.Group, object_type: type[GenericObject]) -> GenericObject:
    "Assumes h5 file is structured the same as the object type"

    # Dict containing the decoded data
    decoded_data = {}

    # Get Key and Type pairs from the given object
    annotations = object_type.__annotations__

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
            elif isinstance(data, np.ndarray) and isinstance(data[0], bytes):
                data = [d.decode() for d in data]

            if data_type == np.datetime64:
                data = np.datetime64(data)
            elif is_namedtuple(data_type) and isinstance(data, str):
                a = data.strip("{}")
                d = dict(item.split(": ") for item in a.split(", "))
                data = data_type(**d)
            elif data_type == dict and isinstance(data, str):
                a = data.strip("{}")
                data = dict(item.split(": ") for item in a.split(", "))
        else:
            if data_type.__name__ == "list":
                sub_type = data_type.__args__[0]
                sub_data = []
                for sub_key in h5_section:
                    # list of dataclass or named tuple
                    if is_dataclass(sub_type) or is_namedtuple(sub_type):
                        sub_data.append(load_object_from_group(h5_section[sub_key], sub_type))
                    else:
                        sub_data.append(h5_section[sub_key])
                data = sub_data
            else:
                # case of a Named tuple or dataclass
                data = load_object_from_group(h5_section, data_type)

        decoded_data[key] = data

    return object_type(**decoded_data)
