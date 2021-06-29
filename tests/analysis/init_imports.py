#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all analysis plugins are imported correctly."""

import unittest

from tests import test_lib


class AnalysisImportTest(test_lib.ImportCheckTestCase):
  """Tests that analysis plugin classes are imported correctly."""

  _IGNORABLE_FILES = frozenset([
      'definitions.py', 'hash_tagging.py', 'interface.py', 'logger.py',
      'manager.py', 'mediator.py'])

  def testAnalysisPluginsImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(
        test_lib.ANALYSIS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
