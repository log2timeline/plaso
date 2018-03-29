#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests that all preprocessors are imported correctly."""

from __future__ import unicode_literals

import os
import unittest

from tests import test_lib


class PreprocessorsImportTest(test_lib.ImportCheckTestCase):
  """Tests that preprocessor classes are imported correctly."""

  _PREPROCESSORS_PATH = os.path.join(os.getcwd(), 'plaso', 'preprocessors')
  _IGNORABLE_FILES = frozenset(
      ['manager.py', 'mediator.py', 'interface.py'])

  def testAnalysisPluginsImported(self):
    """Tests that all preprocessors are imported."""
    self._AssertFilesImportedInInit(
        self._PREPROCESSORS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
