import pathlib
from itertools import islice

import numpy as np

from . import raw_data
from .. import tools


class RawDataInterfaceFactory:
    @tools.profiling.timeing(f'{__name__}.RawDataInterfaceFactory')
    def __init__(self, paths, backends=None, **kwargs):
        self.paths = paths

        global_backend = kwargs.pop('backend', None)
        if backends is None:
            if global_backend is None:
                backends = [None for x in paths]
            else:
                backends = [global_backend for x in paths]
        self.backends = backends

        self.loading_args = kwargs
        self.__current_index = None

    @tools.profiling.timeing(f'{__name__}.RawDataInterfaceFactory')
    def get(self, index):
        return raw_data.RawDataInterface(
            self.paths[index],
            backend=self.backends[index],
            **self.loading_args
        )

    @tools.profiling.timeing(f'{__name__}.RawDataInterfaceFactory')
    def __iter__(self):
        self.__current_index = 0
        for index in range(len(self.paths)):
            yield self.get(index)


@tools.profiling.timeing(f'{__name__}')
def directory_tree(
            path,
            level = -1, 
            limit_to_directories = False,
            length_limit = 1000,
            filter_function = None,
        ):
    '''Create a string that emulates the GNU `tree` tool in pure python. 

    Adapted from: https://stackoverflow.com/a/59109706, CC BY-SA 4.0
    '''

    space = '    '
    branch = '│   '
    tee = '├── '
    last = '└── '

    files = 0
    directories = 0

    out_string = ''

    def inner(dir_path, prefix='', level=-1):
        nonlocal files, directories

        if not level: 
            return  # 0, stop iterating

        if limit_to_directories:
            contents = [d for d in dir_path.iterdir() if d.is_dir()]
        else: 
            contents = [x for x in dir_path.iterdir()]

        if filter_function is not None:
            contents = [x for x in contents if x.is_dir() or filter_function(x)]

        pointers = [tee]*(len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            if path.is_dir():
                yield prefix + pointer + path.name
                directories += 1
                extension = branch if pointer == tee else space 
                yield from inner(path, prefix=prefix + extension, level=level - 1)
            elif not limit_to_directories:
                yield prefix + pointer + path.name
                files += 1

    out_string += path.name + '\n'
    iterator = inner(path, level=level)

    for line in islice(iterator, length_limit):
        out_string += line + '\n'
    if next(iterator, None):
        out_string += f'... length limit, {length_limit}, reached, counted:' + '\n'

    summary = f'{directories} directories' + (f', {files} files' if files else '')
    out_string += summary
    return out_string


class DataStore:

    @tools.profiling.timeing(f'{__name__}.DataStore')
    def __init__(self, path, backends=None):
        self.path = pathlib.Path(path)
        self.backends = backends

        file_list = list(self.path.glob('**/*'))
        backend_list = [None for x in range(len(file_list))]

        for backend, (_, validate) in raw_data.BACKENDS.items():
            if backends is not None:
                if backend not in backends:
                    continue
            for fid, file in enumerate(file_list):
                if backend_list[fid] is not None:
                    continue
                if validate(file):
                    backend_list[fid] = backend

        self.__base_file_list = file_list
        self.__base_supported_filter = np.array([
            True if x is not None else False 
            for x in backend_list
        ])

        self._file_list = [
            x 
            for ix, x in enumerate(file_list) 
            if backend_list[ix] is not None
        ]
        self._backend_list = [
            x 
            for x in backend_list
            if x is not None
        ]

    def __str__(self):
        return f'<DataStore: {len(self._file_list)} files>'

    @tools.profiling.timeing(f'{__name__}.DataStore')
    def tree(self, clean=False, **kwargs):
        if clean:
            def filter_function(path):
                return path in self._file_list

        out_string = directory_tree(
            self.path,
            filter_function = filter_function,
            **kwargs
        )
        l0 = out_string.rfind('\n')
        base = out_string[l0+1:]
        out_string = out_string[:l0+1]
        return f'<DataStore [{base}]\n{out_string}\n>'

    @tools.profiling.timeing(f'{__name__}.DataStore')
    def sort(self, key_function):
        order = np.argsort([key_function(x) for x in self._file_list])
        self.reorder(order)

    @tools.profiling.timeing(f'{__name__}.DataStore')
    def reorder(self, order):
        self._file_list = [self._file_list[ind] for ind in order]
        self._file_list = [self._backend_list[ind] for ind in order]

    @tools.profiling.timeing(f'{__name__}.DataStore')
    def factory(self, selection=None, **kwargs):
        if selection is None:
            selected_files = self._file_list
            selected_backends = self._backend_list
        else:
            selected_files = [self._file_list[ind] for ind in selection]
            selected_backends = [self._backend_list[ind] for ind in selection]

        factory = RawDataInterfaceFactory(
            selected_files, 
            backends=selected_backends, 
            **kwargs
        )
        return factory
