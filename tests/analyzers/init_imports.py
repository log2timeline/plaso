#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all analyzers and hashers are imported correctly."""

from __future__ import unicode_literals

import glob
import os
import unittest

from tests import test_lib


class AnalyzersImportTest(test_lib.ImportCheckTestCase):
  """Tests that analyzer and hasher classes are imported correctly."""

  _ANALYZERS_PATH = os.path.join(os.getcwd(), 'plaso', 'analyzers')
  _IGNORABLE_FILES = frozenset(['logger.py', 'manager.py', 'interface.py'])

  def testAnalyzersImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(self._ANALYZERS_PATH, self._IGNORABLE_FILES)

  def testHashersImported(self):
    """Tests that all plugins are imported."""
    parsers_glob = '{0:s}/*_hashers/'.format(self._ANALYZERS_PATH)
    plugin_directories = glob.glob(parsers_glob)
    for plugin_directory in plugin_directories:
      plugin_directory_path = os.path.join(
          self._ANALYZERS_PATH, plugin_directory)
      self._AssertFilesImportedInInit(
          plugin_directory_path, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
