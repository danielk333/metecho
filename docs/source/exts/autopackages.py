from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import OptionSpec
from sphinx.ext.autosummary import Autosummary

from typing import List
import re
import importlib
from pathlib import Path


python_extensions = ['py', 'pyx']


def autosummary_str(subpackage, module_list, template, toctree):
    autosummary_directive = subpackage + '\n' + '-'*len(subpackage)
    autosummary_directive += f'''
.. automodule::
    {subpackage}

.. autosummary::'''

    if template is not None:
        autosummary_directive += f'\n   :template: {template}'
    if toctree is not None:
        toc = subpackage.replace('.', '/')
        autosummary_directive += f'\n   :toctree: {toctree}/{toc}'

    autosummary_directive += '\n'*2 + '    '
    autosummary_directive += '\n    '.join(module_list)
    return autosummary_directive


def get_module_tree(name, modules):
    package = importlib.import_module(name)
    if not hasattr(package, '__path__'):
        raise AttributeError(f'Given package {name} is not a package or a \
sub-package ({name} has no __path__, most likley a module)')

    path = package.__path__
    path = Path(path) if isinstance(path, str) else Path(path[0])

    files = []
    for ext in python_extensions:
        files += list(path.rglob(f'*.{ext}'))

    top_ind = len(path.parts) - 1
    for file in files:
        sub_package = '.'.join(file.parts[top_ind:-1])
        module = sub_package
        module += '.' + file.stem
        if file.stem == '__init__':
            continue

        if sub_package in modules:
            modules[sub_package].append(module)
        else:
            modules[sub_package] = [module]

    return modules


class AutoAPI(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec: OptionSpec = {
        'toctree': directives.unchanged,
        'template': directives.unchanged,
        'exclude': directives.unchanged,
        'title': directives.unchanged,
    }

    def run(self) -> List[Node]:
        names = [
            x.strip().split()[0] for x in self.content
            if x.strip() and re.search(r'^[~a-zA-Z_]', x.strip()[0])
        ]
        onodes = []

        onodes.append(nodes.title(
            text=self.options.get('title', 'Sub-packages')
        ))
        if 'autopackages_toctree' in self.config:
            out_dir = self.config['autopackages_toctree']
        else:
            out_dir = 'autopackages'
        out_dir = Path('./source/' + out_dir).resolve()
        out_dir.mkdir(exist_ok=True)

        module_tree = {}
        for name in names:
            module_tree = get_module_tree(name, module_tree)

        toctree = self.options.get('toctree', None)
        template = self.options.get('template', None)

        for subpackage, modules in module_tree.items():
            onodes.append(nodes.subtitle(text=subpackage))
            toc = subpackage.replace('.', '/')
            with open(out_dir / (subpackage + '.rst'), 'w') as fh:
                fh.write(autosummary_str(subpackage, modules, template, toctree))

        return onodes


def setup(app):
    app.add_directive("autoapi", AutoAPI)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
