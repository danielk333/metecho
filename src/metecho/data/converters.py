import logging
from collections import OrderedDict

import numpy as np

logger = logging.getLogger(__name__)

CONVERTERS = OrderedDict()


def list_converters():
    st = ""
    for name in CONVERTERS:
        st += f"{name}:\n"
        for backend in CONVERTERS[name]:
            if backend == "validator":
                st += "├Validator> present\n"
            else:
                st += f"├Backend> {backend}\n"
    return st


def converter(name, backend):
    """Decorator to register function as a convert to a backend format

    #TODO: add descripiton of backend load function here (what it should return ect)
    """

    def converter_wrapper(func):
        logger.debug(f"Registering converter from {name} to {backend} backend")
        if name in CONVERTERS:
            CONVERTERS[name][backend] = func
        else:
            CONVERTERS[name] = {backend: func}
        return func

    return converter_wrapper


def converter_validator(name):
    """Decorator to register function as a converter validator

    #TODO: add descripiton of backend load function here (what it should return ect)
    """

    def converter_wrapper(func):
        logger.debug(f"Registering validator for {name} backend")
        if name in CONVERTERS:
            CONVERTERS[name]["validator"] = func
        else:
            CONVERTERS[name] = {"validator": func}
        return func

    return converter_wrapper


def check_if_convertable(path):
    """Checks if the given path can be converted to a supported backend and 
    returns the detected format, else returns None.
    """
    for fmt, backends in CONVERTERS.items():
        if "validator" not in backends:
            continue
        validator = backends["validator"]
        if validator(path):
            return fmt
    return None


def convert(input_files, output_location, backend=None, input_format=None, **kwargs):
    """Convert given list of input files or input file to a supported
    backend format and returns the created data files.
    """
    if len(input_files) == 0:
        return []

    files_created = None
    if input_format is None:
        format_found = False

        for fmt, backends in CONVERTERS.items():
            if "validator" not in backends:
                continue
            validator = backends["validator"]
            valid = [validator(file) for file in input_files]
            if np.any(valid):
                sub_files = [input_files[x] for x in np.argwhere(valid).flatten()]
                if backend is None:
                    use_backend = None
                    for key in backends:
                        if key == "validator":
                            continue
                        use_backend = key

                elif backend not in backends:
                    raise ValueError(
                        f'No converter to the given backend \
                        "{backend}" found for given input path type "{fmt}"\n \
                        Files affected: {sub_files}'
                    )
                else:
                    use_backend = backend

                logger.info(
                    f"Converting {len(sub_files)} from {fmt} to {use_backend}..."
                )

                func = backends[use_backend]

                files_created = func(sub_files, output_location, **kwargs)
                format_found = True
                break
            else:
                continue

        if not format_found:
            raise ValueError("No converter found for given input path")
    else:
        if input_format not in CONVERTERS:
            raise ValueError(f"Given input format {input_format} has no converters")

        backends = CONVERTERS[input_format]
        if backend is None:
            use_backend = None
            for key in backends:
                if key == "validator":
                    continue
                use_backend = key
        else:
            use_backend = backend

        logger.info(
            f"Converting {len(input_files)} from {input_format} to {use_backend}..."
        )
        func = CONVERTERS[input_format][use_backend]
        files_created = func(input_files, output_location, **kwargs)

    return files_created
