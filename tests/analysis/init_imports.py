#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all analysis plugins are imported correctly."""

from __future__ import unicode_literals

import unittest

from tests import test_lib


class AnalysisImportTest(test_lib.ImportCheckTestCase):
  """Tests that analysis plugin classes are imported correctly."""

  _IGNORABLE_FILES = frozenset([
      'logger.py', 'manager.py', 'definitions.py', 'mediator.py',
      'interface.py'])

  def testAnalysisPluginsImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(
        test_lib.ANALYSIS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
