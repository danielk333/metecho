import setuptools
import codecs
import os.path
from distutils.core import Extension


with open('README.md', 'r') as fh:
    long_description = fh.read()

# from
# https://packaging.python.org/guides/single-sourcing-package-version/#single-sourcing-the-version


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


libxcorr = Extension(
    name='metecho.generalized_matched_filter.libxcorr',
    sources=['src/libxcorr/libxcorr.c'],
    include_dirs=['src/libxcorr/'],
)


setuptools.setup(
    version=get_version("src/metecho/version.py"),
    ext_modules=[libxcorr],
)
