from docutils.nodes import Node
from docutils.parsers.rst import directives
# from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import OptionSpec
from sphinx.directives.other import TocTree

from typing import List
import re
import importlib
from pathlib import Path

'''
TODO: make sure this works with a rst from any subdirectory (and not just next to conf.py)
'''


python_extensions = ['py', 'pyx']
title_chars = {
    'section': '=',
    'subsection': '-',
    'subsubsection': '^',
}


def generate_toc_directive(autopackages_dir, fname):
    toc_directive = f'''
.. toctree::
    :maxdepth: 3

    '''
    content = [f'{autopackages_dir}/{fname}']
    toc_directive += '    ' + '\n    '.join(content)
    return toc_directive, content


def generate_autosummary_rst(subpackage, module_list, template, toctree, title_char):
    autosummary_directive = subpackage + '\n' + title_char*len(subpackage)
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


def get_module_tree(name):
    package = importlib.import_module(name)
    if not hasattr(package, '__path__'):
        raise AttributeError(f'Given package {name} is not a package or a \
sub-package ({name} has no __path__, most likley a module)')

    path = package.__path__
    path = Path(path) if isinstance(path, str) else Path(path[0])

    files = []
    for ext in python_extensions:
        files += list(path.rglob(f'*.{ext}'))

    name_ind = len(name.split('.'))
    top_ind = len(path.parts) - name_ind

    module_tree = {}
    for file in files:
        sub_package = '.'.join(file.parts[top_ind:-1])
        module = sub_package
        if file.stem != '__init__':
            module += '.' + file.stem

        if sub_package in module_tree:
            module_tree[sub_package].append(module)
        else:
            module_tree[sub_package] = [module]

    for sub_package in module_tree:
        module_tree[sub_package].sort()
    return module_tree


class AutoPackages(SphinxDirective):
    has_content = True
    required_arguments = 1
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
        assert len(self.arguments) > 0, 'output file name needed as argument'
        fname = self.arguments[0]
        names = [
            x.strip().split()[0] for x in self.content
            if x.strip() and re.search(r'^[~a-zA-Z_]', x.strip()[0])
        ]

        autopackages_dir = self.config['autopackages_toctree']
        src_dir = Path(self.env.srcdir)
        out_dir = (src_dir / autopackages_dir).resolve()
        out_dir.mkdir(exist_ok=True)

        level_diff = len(out_dir.parts) - len(src_dir.parts)

        title = self.options.get('title', None)
        template = self.options.get('template', None)
        toctree = self.options.get('toctree', 'autosummary')
        excludes = self.options.get('exclude', '').split()
        toctree = '../'*level_diff + toctree

        h1 = title_chars['section']
        h2 = title_chars['subsection'] if title is None else title_chars['section']
        h3 = title_chars['subsubsection'] if title is None else title_chars['subsection']

        src_content = ''
        if title is not None:
            src_content += title + '\n'
            src_content += h1*len(title) + '\n'*2
        for name in names:
            module_tree = get_module_tree(name)
            for exclude in excludes:
                if exclude in module_tree:
                    module_tree.pop(exclude)
            if name not in module_tree:
                continue
            modules = module_tree.pop(name)

            src_content += generate_autosummary_rst(
                name, 
                modules, 
                template, 
                toctree,
                h2,
            )
            src_content += '\n'*2

            if len(module_tree) > 0:
                src_content += 'Sub-packages' + '\n'
                src_content += h2*len('Sub-packages') + '\n'*2

            for subpackage, modules in module_tree.items():
                src_content += generate_autosummary_rst(
                    subpackage, 
                    modules, 
                    template, 
                    toctree,
                    h3,
                )
                src_content += '\n'*2
        with open(out_dir / (fname + '.rst'), 'w') as fh:
            fh.write(src_content)

        block_text, content = generate_toc_directive(autopackages_dir, fname)
        toc = TocTree(
            name = self.name, 
            arguments = [], 
            options = {
                'maxdepth': 3,
            }, 
            content = content, 
            lineno = self.lineno,
            content_offset = self.content_offset, 
            block_text = block_text, 
            state = self.state, 
            state_machine = self.state_machine,
        )

        out_nodes = toc.run()

        return out_nodes


def setup(app):
    app.add_directive("autopackages", AutoPackages)
    app.add_config_value('autopackages_toctree', 'autopackages', True)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
