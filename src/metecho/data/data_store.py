"""
Data storage module
===================

This module contains systems to handle file-structures of radar raw data.
"""
import pathlib

import numpy as np

from . import raw_data
from . import converters


class RawDataInterfaceFactory:
    """A class for iterating trough a list of `RawDataInterface`s that
    instantiates and load them in sequence, used to substantially
    reduce memory footprint.

    Parameters
    ----------
    paths: list(pathlib.Path)
        List of raw data file paths
    backends: list(str), optional
        List of backends for each given file, if not given a valid backend
        is found all registered backends.
    backend: str, optional
        Backend used for all files, ignored if `backends` is given.
    **kwargs: dict, optional
        All additional keyword arguments are passed on to the
        `RawDataInterface` instantiation.

    Attributes
    ----------
    paths: list(pathlib.Path)
        List of raw data file paths
    backends: list(str):
        List of backends for each given file
    loading_args: dict
        Keyword arguemnts passed to the `RawDataInterface` instantiation.
    """

    def __init__(self, paths, backends=None, **kwargs):
        self.paths = paths

        global_backend = kwargs.pop("backend", None)
        if backends is None:
            if global_backend is None:
                backends = [None for x in paths]
            else:
                backends = [global_backend for x in paths]
        self.backends = backends

        self.loading_args = kwargs
        self.__current_index = None

    def get(self, index):
        """Get `RawDataInterface` for path with given index in the list of paths."""
        return raw_data.RawDataInterface(
            self.paths[index], backend=self.backends[index], **self.loading_args
        )

    def __iter__(self):
        """Iterate trough all paths and yield the `RawDataInterface`."""
        self.__current_index = 0
        for index in range(len(self.paths)):
            yield self.get(index)


def directory_tree(
    path,
    level=-1,
    limit_to_directories=False,
    length_limit=1000,
    filter_function=None,
    skip_empty_directories=True,
):
    """Create a string that emulates the GNU `tree` tool in pure python."""

    space = "   "
    branch = "│  "
    tee = "├─ "
    last = "└─ "

    files = 0
    directories = 0

    if not path.is_dir():
        raise ValueError(f'Given input path "{path}" is not a directory')

    def recursive_walk(pth, lv, size):
        f, d = 0, 0
        if lv == level:
            return [], 0, 0
        ls = list(pth.glob("*"))
        st = []
        for ind, item in enumerate(ls):
            sym, cont = (last, space) if ind == len(ls) - 1 else (tee, branch)
            if len(st) + size >= length_limit:
                break
            if item.is_dir():
                d += 1
                below, bf, bd = recursive_walk(item, lv + 1, len(st) + size + 1)
                f += bf
                d += bd
                if skip_empty_directories and bf == 0:
                    continue
                st += [sym + item.name]
                for x in below:
                    st += [cont + x]
            else:
                if filter_function is not None:
                    if not filter_function(item):
                        continue
                f += 1
                if limit_to_directories:
                    continue
                st += [sym + item.name]
        return st, f, d

    out_string, files, directories = recursive_walk(path, 0, 0)

    if len(out_string) >= length_limit:
        out_string.append("Maximum listing length reached...")
    out_string = path.name + "\n" + "\n".join(out_string) + "\n"

    summary = f"{directories} directories" + (f", {files} files" if files else "")
    out_string += summary
    return out_string


class DataStore:
    def __init__(self, path, backends=None, include_convertable=False):
        self.path = pathlib.Path(path)
        self.backends = backends
        self.include_convertable = include_convertable
        self.reload()

    def reload(self):
        file_list = list(x for x in self.path.glob("**/*") if x.is_file())
        backend_list = [None for x in range(len(file_list))]
        converter_list = [None for x in range(len(file_list))]

        for backend, (_, validate) in raw_data.BACKENDS.items():
            if self.backends is not None:
                if backend not in self.backends:
                    continue
            for fid, file in enumerate(file_list):
                if backend_list[fid] is not None:
                    continue
                if validate(file):
                    backend_list[fid] = backend

        if self.include_convertable:
            for fid, file in enumerate(file_list):
                # Only check files that do not have a backend
                if backend_list[fid] is not None:
                    continue

                for fmt, to_backend in converters.CONVERTERS.items():
                    if "validator" not in to_backend:
                        continue
                    validator = to_backend["validator"]
                    if validator(file):
                        converter_list[fid] = fmt

        self.__base_file_list = file_list
        self.__base_supported_filter = np.array(
            [True if x is not None else False for x in converter_list]
        )
        self.__base_convertable_filter = np.array(
            [True if x is not None else False for x in backend_list]
        )

        self._file_list = [
            x for ix, x in enumerate(file_list) if backend_list[ix] is not None
        ]
        self._backend_list = [x for x in backend_list if x is not None]
        self._convertable_file_list = [
            x for ix, x in enumerate(file_list) if converter_list[ix] is not None
        ]
        self._convertable_format_list = [x for x in converter_list if x is not None]

    def __str__(self):
        return f"<DataStore: {len(self._file_list)} files>"

    def get_files(self):
        return zip(self._file_list, self._backend_list)

    def get_convertable(self):
        return zip(self._convertable_file_list, self._convertable_format_list)

    def tree(self, clean=False, **kwargs):
        if clean:

            def filter_function(path):
                return path in self._file_list

        else:
            filter_function = None

        out_string = directory_tree(
            self.path, filter_function=filter_function, **kwargs
        )
        l0 = out_string.rfind("\n")
        out_string = f"Raw data: [{out_string[l0+1:]}]\n{out_string[:l0+1]}"

        if clean and self.include_convertable:

            def filter_function_convert(path):
                return path in self._convertable_file_list

            out_string_convert = directory_tree(
                self.path, filter_function=filter_function_convert, **kwargs
            )
            l0 = out_string_convert.rfind("\n")
            out_string_convert = f"\nConvertable: [{out_string_convert[l0+1:]}]\n{out_string_convert[:l0+1]}"
        else:
            out_string_convert = ""

        return f"<DataStore {out_string}{out_string_convert}\n>"

    def sort(self, key_function):
        order = np.argsort([key_function(x) for x in self._file_list])
        self.reorder(order)

    def reorder(self, order):
        self._file_list = [self._file_list[ind] for ind in order]
        self._backend_list = [self._backend_list[ind] for ind in order]

    def convert(
        self,
        output_location,
        backend,
        selection=None,
        path_format_filter=None,
        **kwargs,
    ):
        if selection is None:
            selected_files = self._convertable_file_list
            selected_formats = self._convertable_format_list
        else:
            selected_files = [self._convertable_file_list[ind] for ind in selection]
            selected_formats = [self._convertable_format_list[ind] for ind in selection]

        if path_format_filter is not None:
            selected_tupes = [
                (pth, fmt)
                for pth, fmt in zip(selected_files, selected_formats)
                if path_format_filter(pth, fmt)
            ]
            selected_files, selected_formats = zip(*selected_tupes)

        ret = converters.convert(
            selected_files, output_location, backend=backend, **kwargs
        )
        return ret

    def factory(self, selection=None, path_backend_filter=None, **kwargs):
        if selection is None:
            selected_files = self._file_list
            selected_backends = self._backend_list
        else:
            selected_files = [self._file_list[ind] for ind in selection]
            selected_backends = [self._backend_list[ind] for ind in selection]

        if path_backend_filter is not None:
            selected_tupes = [
                (pth, back)
                for pth, back in zip(selected_files, selected_backends)
                if path_backend_filter(pth, back)
            ]
            selected_files, selected_backends = zip(*selected_tupes)

        factory = RawDataInterfaceFactory(
            selected_files, backends=selected_backends, **kwargs
        )
        return factory
