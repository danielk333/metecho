# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import warnings
from datetime import date
import sys
import pathlib

import metecho

# According to non-pypi extensions
# Ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-extensions
ext_paths = (pathlib.Path(__file__).parent / 'extensions').resolve()
sys.path.append(str(ext_paths))

# -- Project information -----------------------------------------------------

project = 'metecho'
version = '.'.join(metecho.__version__.split('.')[:2])
release = metecho.__version__

copyright = f'[2022-{date.today().year}] Daniel Kastinen, Kenneth Kullbrandt'
author = 'Daniel Kastinen, Kenneth Kullbrandt'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'm2r2',
    'irf.autopackages',
    'nbsphinx',
    'sphinx_gallery.load_style',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'numpydoc',
    'sphinx_gallery.gen_gallery',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'basic'
html_css_files = [
    'https://www.irf.se/branding/irf.css',
    'https://www.irf.se/branding/irf-sphinx-basic.css',
]
html_logo = 'static/logo.png'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['static']

# Remove matplotlib agg warnings from generated doc when using plt.show
warnings.filterwarnings("ignore", category=UserWarning,
    message='Matplotlib is currently using agg, which is a'
            ' non-GUI backend, so cannot show the figure.')


# -- Options for gallery extension ---------------------------------------
sphinx_gallery_conf = {
     'examples_dirs': '../../examples',   # path to your example scripts
     'gallery_dirs': 'autogallery',  # path where to save gallery generated examples
     'filename_pattern': '/*.py',
     'ignore_pattern': r'.*__no_gallery\.py',
}

nbsphinx_kernel_name = 'python3'

# Autopackages settings
irf_autopackages_toctree = 'autopackages'

# Napoleon settings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_custom_sections = None

# -----------------------------------------------------------------------------
# Autosummary
# -----------------------------------------------------------------------------

autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = False

# -----------------------------------------------------------------------------
# Intersphinx configuration
# -----------------------------------------------------------------------------
intersphinx_mapping = {
    'numpy': ('https://docs.scipy.org/doc/numpy', None),
    'scipy': ('http://docs.scipy.org/doc/scipy/reference/', None),
    'matplotlib': ('http://matplotlib.sourceforge.net/', None),
}
