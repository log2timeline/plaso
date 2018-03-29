#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests that all parsers and plugins are imported correctly."""

from __future__ import unicode_literals

import glob
import os
import unittest

from tests import test_lib


class ParserImportTest(test_lib.ImportCheckTestCase):
  """Tests that parser classes are imported correctly."""

  _PARSERS_PATH = os.path.join(os.getcwd(), 'plaso', 'parsers')
  _IGNORABLE_FILES = frozenset(
      ['manager.py', 'presets.py', 'mediator.py', 'interface.py', 'plugins.py'])

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
