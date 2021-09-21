import setuptools
import codecs
import os.path


with open('requirements', 'r') as fh:
    pip_req = fh.read().split('\n')
    pip_req = [x.strip() for x in pip_req if len(x.strip()) > 0]

with open('README.md', 'r') as fh:
    long_description = fh.read()

#from
#https://packaging.python.org/guides/single-sourcing-package-version/#single-sourcing-the-version
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


setuptools.setup(
    name = 'metecho',
    version = get_version("metecho/version.py"),
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/danielk333/metecho',
    classifiers = [
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Development Status :: 4 - Beta',
    ],
    python_requires = '>=3.0',
    install_requires = pip_req,
    packages = setuptools.find_packages(),
    # metadata to display on PyPI
    author = 'Daniel Kastinen',
    author_email = 'daniel.kastinen@irf.se',
    description = 'Keplerian orbit functions in Python',
    license = 'MIT',
)
