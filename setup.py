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
)


setuptools.setup(
    name='metecho',
    version=get_version("src/metecho/version.py"),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/danielk333/metecho',
    entry_points={
        'console_scripts': [
            'metecho = metecho.cli:main'
        ],
    },
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
        "mpi": [
            "mpi4py>=3.1.1",
        ],
        "develop": [
            "pytest>=5.2.2",
            "sphinx>=4.4.0",
            "sphinx-gallery>=0.10.1",
            "flake8 >= 4.0.1",
            "wheel >= 0.37.0",
            "build >= 0.7.0",
            "twine >= 3.4.2",
            "coverage >= 6.0.2",
        ]
    },
    package_dir={
        "": "src"
    },
    packages=setuptools.find_packages(where="src"),
    package_data={"": [
        "src/libxcorr/*", 
    ]},
    include_package_data=True,
    ext_modules=[libxcorr],
    # metadata to display on PyPI
    author='Daniel Kastinen, Kenneth Kullbrandt',
    author_email='daniel.kastinen@irf.se',
    description='Radar meteor analysis in Python and C',
    license='MIT'
)
