import logging
from collections import OrderedDict

import numpy as np

from .. import tools

logger = logging.getLogger(__name__)

CONVERTERS = OrderedDict()


@tools.profiling.timeing(f'{__name__}')
def list_converters():
    st = ''
    for name in CONVERTERS:
        st += f'{name}:\n'
        for backend in CONVERTERS[name]:
            if backend == 'validator':
                st += '├Validator> present\n'
            else:
                st += f'├Backend> {backend}\n'
    return st


@tools.profiling.timeing(f'{__name__}')
def converter(name, backend):
    '''Decorator to register function as a convert to a backend format

    #TODO: add descripiton of backend load function here (what it should return ect)
    '''

    def converter_wrapper(func):
        logger.debug(f'Registering converter from {name} to {backend} backend')
        global CONVERTERS
        if name in CONVERTERS:
            CONVERTERS[name][backend] = func
        else:
            CONVERTERS[name] = {backend: func}
        return func

    return converter_wrapper


@tools.profiling.timeing(f'{__name__}')
def converter_validator(name):
    '''Decorator to register function as a converter validator

    #TODO: add descripiton of backend load function here (what it should return ect)
    '''

    def converter_wrapper(func):
        logger.debug(f'Registering validator for {name} backend')
        global CONVERTERS
        if name in CONVERTERS:
            CONVERTERS[name]['validator'] = func
        else:
            CONVERTERS[name] = {'validator': func}
        return func

    return converter_wrapper


@tools.profiling.timeing(f'{__name__}')
def convert(input_files, output_location, backend, input_format=None, **kwargs):
    '''Convert given list of input files or input file to a supported backend format.
    '''

    ret = None
    if input_format is None:
        format_found = False

        for fmt, backends in CONVERTERS.items():
            if 'validator' not in backends:
                continue
            validator = backends['validator']
            valid = [validator(file) for file in input_files]
            if np.any(valid):
                sub_files = [input_files[x] for x in np.argwhere(valid).flatten()]
                if backend not in backends:
                    raise ValueError(
                        f'No converter to the given backend \
                        "{backend}" found for given input path type "{fmt}"\n \
                        Files affected: {sub_files}'
                    )

                logger.info(f'Converting {len(sub_files)} from {fmt} to {backend}...')

                func = backends[backend]

                ret = func(sub_files, output_location, **kwargs)
                format_found = True
                break
            else:
                continue

        if not format_found:
            raise ValueError('No converter found for given input path')
    else:
        if input_format not in CONVERTERS:
            raise ValueError(f'Given input format {input_format} has no converters')

        logger.info(f'Converting {len(input_files)} from {input_format} to {backend}...')
        func = CONVERTERS[input_format][backend]
        ret = func(input_files, output_location, **kwargs)

    return ret
