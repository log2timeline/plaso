#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all CLI helpers are imported correctly."""

import unittest

from tests import test_lib


class CLIHelperImportTest(test_lib.ImportCheckTestCase):
  """Tests that CLI helper classes are imported correctly."""

  _IGNORABLE_FILES = frozenset(['manager.py', 'interface.py'])

  def testCLIHelpersImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(
        test_lib.CLI_HELPERS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
