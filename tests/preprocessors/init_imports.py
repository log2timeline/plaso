#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all preprocessors are imported correctly."""

import unittest

from tests import test_lib


class PreprocessorsImportTest(test_lib.ImportCheckTestCase):
  """Tests that preprocessor classes are imported correctly."""

  _IGNORABLE_FILES = frozenset([
      'logger.py', 'manager.py', 'mediator.py', 'interface.py'])

  def testAnalysisPluginsImported(self):
    """Tests that all preprocessors are imported."""
    self._AssertFilesImportedInInit(
        test_lib.PREPROCESSORS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
