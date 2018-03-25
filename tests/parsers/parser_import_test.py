#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests that all parsers and plugins are imported correctly."""

from __future__ import unicode_literals

import io
import glob
import os
import re
import unittest

from tests import test_lib


class ParserImportTest(test_lib.BaseTestCase):
  """Tests that parser classes are imported correctly."""

  _PARSERS_PATH = os.path.join(os.getcwd(), 'plaso', 'parsers')
  _FILENAME_REGEXP = re.compile(r'^[^_]*\.py$')
  _IGNORABLE_FILES = frozenset(
      ['manager.py', 'presets.py', 'mediator.py', 'interface.py', 'plugins.py'])

  def _AssertFilesImportedInInit(self, path, ignorable_files):
    """Checks that files in path are imported in __init__.py

    Args:
      path (str): path to directory containing an __init__.py file and other
          Python files which should be imported.
      ignorable_files (list[str]): names of Python files that don't need to
          appear in __init__.py. For example, 'manager.py'.
    """
    init_path = '{0:s}/__init__.py'.format(path)
    with io.open(init_path, mode='r', encoding='utf-8') as init_file:
      init_content = init_file.read()

    for file_path in os.listdir(path):
      filename = os.path.basename(file_path)
      if filename in ignorable_files:
        continue
      if self._FILENAME_REGEXP.search(filename):
        import_name, _, _ = filename.partition('.')
        import_expression = re.compile(r' import {0:s}\b'.format(import_name))

        # pylint: disable=deprecated-method
        self.assertRegexpMatches(
            init_content, import_expression,
            '{0:s} not imported in {1:s}'.format(import_name, init_path))

  def testParsersImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(self._PARSERS_PATH, self._IGNORABLE_FILES)

  def testPluginsImported(self):
    """Tests that all plugins are imported."""
    parsers_glob = '{0:s}/*_plugins/'.format(self._PARSERS_PATH)
    plugin_directories = glob.glob(parsers_glob)
    for plugin_directory in plugin_directories:
      plugin_directory_path = os.path.join(
          self._PARSERS_PATH, plugin_directory)
      self._AssertFilesImportedInInit(
          plugin_directory_path, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
