import setuptools
import codecs
import os.path
from distutils.core import Extension


with open('requirements', 'r') as fh:
    pip_req = fh.read().split('\n')
    pip_req = [x.strip() for x in pip_req if len(x.strip()) > 0]

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


libecho = Extension(name='metecho.generalized_matched_filter.libecho',
                    sources=['metecho/generalized_matched_filter/xcorr_echo_search.c']
                    )


setuptools.setup(
    name='metecho',
    version=get_version("metecho/version.py"),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/danielk333/metecho',
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Development Status :: 4 - Beta',
    ],
    python_requires='>=3.0',
    install_requires=[
        "h5py>=3.4.0",
        "matplotlib>=2.2.2",
        "numpy>=1.14.3",
        "scipy>=1.1.0",
        "tabulate>=0.8.7",
        "tqdm>=4.46.0",
    ],
    extras_require={
        "mpi": ["mpi4py>=3.1.1"]
    },
    packages=setuptools.find_packages(),
    ext_modules=[libecho],
    # metadata to display on PyPI
    author='Daniel Kastinen',
    author_email='daniel.kastinen@irf.se',
    description='Keplerian orbit functions in Python',
    license='MIT'
)
