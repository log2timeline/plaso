# -*- coding: utf-8 -*-
"""Sphinx build configuration file."""

import os
import sys

from sphinx.ext import apidoc

from docutils import nodes
from docutils import transforms

# Change PYTHONPATH to include plaso module and dependencies.
sys.path.insert(0, os.path.abspath('..'))

import plaso  # pylint: disable=wrong-import-position

import utils.dependencies  # pylint: disable=wrong-import-position


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '2.0.1'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'recommonmark',
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_markdown_tables',
    'sphinx_rtd_theme',
]

# We cannot install architecture dependent Python modules on readthedocs,
# therefore we mock most imports.
pip_installed_modules = set(['pyparsing'])

dependency_helper = utils.dependencies.DependencyHelper(
    dependencies_file=os.path.join('..', 'dependencies.ini'),
    test_dependencies_file=os.path.join('..', 'test_dependencies.ini'))
modules_to_mock = set(dependency_helper.dependencies.keys())
modules_to_mock = modules_to_mock.difference(pip_installed_modules)

autodoc_mock_imports = sorted(modules_to_mock)

# Options for the Sphinx Napoleon extension, which reads Google-style
# docstrings.
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# General information about the project.
# pylint: disable=redefined-builtin
project = 'Plaso (log2timeline)'
copyright = 'The Plaso (log2timeline) authors'
version = plaso.__version__
release = plaso.__version__

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

# The master toctree document.
master_doc = 'index'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Output file base name for HTML help builder.
htmlhelp_basename = 'plasodoc'


# -- Options linkcheck ----------------------------------------------------

linkcheck_ignore = [
    '[^#/]*#',
    '(|[.][.]/)api/[^#]*#',
    '(|[.][.]/)developer/[^#]*#',
    '(|[.][.]/)user/[^#]*#',
    # The docs.github.com are known to be flaky.
    'https://docs.github.com/.*',
    'https://github.com/libyal/libsigscan/wiki/Internals#',
    'https://github.com/log2timeline/dfvfs/wiki#',
    'https://groups.google.com/forum/#',
    'https://developers.virustotal.com/reference#',
]


# -- Code to rewrite links for readthedocs --------------------------------

# This function is a Sphinx core event callback, the format of which is detailed
# here: https://www.sphinx-doc.org/en/master/extdev/appapi.html#events

# pylint: disable=unused-argument
def RunSphinxAPIDoc(app):
  """Runs sphinx-apidoc to auto-generate documentation.

  Args:
    app (sphinx.application.Sphinx): Sphinx application. Required by the
        the Sphinx event callback API.
  """
  current_directory = os.path.abspath(os.path.dirname(__file__))
  module_path = os.path.join(current_directory, '..', 'plaso')
  api_directory = os.path.join(current_directory, 'sources', 'api')
  apidoc.main(['-o', api_directory, module_path, '--force'])


class MarkdownLinkFixer(transforms.Transform):
  """Transform definition to parse .md references to internal pages."""

  default_priority = 1000

  _URI_PREFIXES = [
      'https://github.com/log2timeline/l2tdocs/blob/',
      'https://github.com/log2timeline/l2tbinaries/blob/',
      'https://github.com/google/timesketch/blob/']

  def _FixLinks(self, node):
    """Corrects links to .md files not part of the documentation.

    Args:
      node (docutils.nodes.Node): docutils node.

    Returns:
      docutils.nodes.Node: docutils node, with correct URIs outside
          of Markdown pages outside the documentation.
    """
    if isinstance(node, nodes.reference) and 'refuri' in node:
      reference_uri = node['refuri']
      for uri_prefix in self._URI_PREFIXES:
        if (reference_uri.startswith(uri_prefix) and not (
            reference_uri.endswith('.asciidoc') or
            reference_uri.endswith('.md'))):
          node['refuri'] = reference_uri + '.md'
          break

    return node

  def _Traverse(self, node):
    """Traverses the document tree rooted at node.

    Args:
      node (docutils.nodes.Node): docutils node.
    """
    self._FixLinks(node)

    for child_node in node.children:
      self._Traverse(child_node)

  # pylint: disable=arguments-differ
  def apply(self):
    """Applies this transform on document tree."""
    self._Traverse(self.document)


# pylint: invalid-name
def setup(app):
  """Called at Sphinx initialization.

  Args:
    app (sphinx.application.Sphinx): Sphinx application.
  """
  # Triggers sphinx-apidoc to generate API documentation.
  app.connect('builder-inited', RunSphinxAPIDoc)
  app.add_config_value(
      'recommonmark_config', {'enable_auto_toc_tree': True}, True)
  app.add_transform(MarkdownLinkFixer)
