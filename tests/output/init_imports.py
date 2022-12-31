#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all output modules are imported correctly."""

import unittest

from tests import test_lib


class OutputImportTest(test_lib.ImportCheckTestCase):
  """Tests that analysis plugin classes are imported correctly."""

  _IGNORABLE_FILES = frozenset([
      'formatting_helper.py', 'interface.py', 'logger.py', 'manager.py',
      'mediator.py', 'shared_dsv.py', 'shared_json.py', 'shared_opensearch.py',
      'text_file.py', 'winevt_rc.py'])

  def testOutputModulesImported(self):
    """Tests that all output modules are imported."""
    self._AssertFilesImportedInInit(test_lib.OUTPUT_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
