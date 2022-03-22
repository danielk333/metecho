from collections import OrderedDict
from typing import List
import re
import importlib
from pathlib import Path

import docutils.nodes as nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.misc import Include
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import OptionSpec


python_extensions = ['py', 'pyx']
title_chars = {
    'section': '=',
    'subsection': '-',
    'subsubsection': '^',
}


def generate_autosummary_directive(
                subpackage, module_list, 
                template, toctree, 
                title_char, title = None,
            ):
    '''Generate an autosummary rst directive that includes all subpackages 
    and leads with an automodule of the top package.
    '''
    autosummary_directive = ''

    if title is None:
        title = subpackage.split('.')[-1]
    if len(title) > 0:
        autosummary_directive += title + '\n' + title_char*len(title)

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
    '''Uses an importable name to find the underlying structure of python files
    of that package and groups the modules according to subpackage.
    '''
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
        module += '.' + file.stem
        if file.stem == '__init__':
            continue

        if sub_package in module_tree:
            module_tree[sub_package].append(module)
        else:
            module_tree[sub_package] = [module]

    for sub_package in module_tree:
        module_tree[sub_package].sort()
    
    module_tree = OrderedDict(sorted(module_tree.items()))
    return module_tree


class AutoPackages(SphinxDirective):
    '''Automatically genereate rst-files similar to autosummary but for the 
    subpackage structure of the input content. The rst file is saved to the 
    filename in the first rst argument.
    '''
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

    def run(self) -> List[nodes.Node]:
        assert len(self.arguments) > 0, 'output file name needed as argument'
        fname = self.arguments[0]
        names = [
            x.strip().split()[0] for x in self.content
            if x.strip() and re.search(r'^[~a-zA-Z_]', x.strip()[0])
        ]

        autopackages_dir = self.config['irf_autopackages_toctree']
        src_dir = Path(self.env.srcdir)
        source_file = (src_dir / self.env.docname).resolve()
        out_dir = (src_dir / autopackages_dir).resolve()
        out_dir.mkdir(exist_ok=True)
        out_rst = out_dir / (fname + '.rst')

        level_diff = len(out_dir.parts) - len(source_file.parts)

        title = self.options.get('title', None)
        depth = self.options.get('tocdepth', 2)
        template = self.options.get('template', None)
        toctree = self.options.get('toctree', 'autosummary')
        excludes = self.options.get('exclude', '').split()
        toctree = '../'*level_diff + toctree

        h1 = title_chars['section']
        h2 = title_chars['subsection']
        h3 = title_chars['subsubsection']

        src_content = ''
        for name in names:
            module_tree = get_module_tree(name)

            # Exclude subpackages and modules according to option
            for exclude in excludes:
                if exclude in module_tree:
                    module_tree.pop(exclude)
            for subpackage, modules in module_tree.items():
                for exclude in excludes:
                    if exclude in modules:
                        modules.remove(exclude)

            # Subpackage was removed, skip
            if name not in module_tree:
                continue

            # Autosummary the top level
            modules = module_tree.pop(name)
            if len(modules) > 0:
                src_content += generate_autosummary_directive(
                    name, 
                    modules, 
                    template, 
                    toctree,
                    h1,
                    title=title
                )
            else:
                _title = name.split('.')[-1] if title is None else title
                src_content = _title + '\n' + h1*len(_title)
            src_content += '\n'*2

            # If there are subpackages, autosummary them
            if len(module_tree) > 0:
                src_content += 'Sub-packages' + '\n'
                src_content += h2*len('Sub-packages') + '\n'*2

            for subpackage, modules in module_tree.items():
                src_content += generate_autosummary_directive(
                    subpackage, 
                    modules, 
                    template, 
                    toctree,
                    h3,
                )
                src_content += '\n'*2

        with open(out_rst, 'w') as fh:
            fh.write(src_content)

        # Include the autopackages outputs
        toc = Include(
            name = self.name, 
            arguments = [f'{autopackages_dir}/{fname}.rst'], 
            options = {}, 
            content = None, 
            lineno = self.lineno,
            content_offset = self.content_offset, 
            block_text = '', 
            state = self.state, 
            state_machine = self.state_machine,
        )

        out_nodes = toc.run()
        return out_nodes


def setup(app):
    app.add_directive("irf_autopackages", AutoPackages)
    app.add_config_value('irf_autopackages_toctree', 'autopackages', True)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
