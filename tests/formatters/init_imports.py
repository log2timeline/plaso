#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all formatters are imported correctly."""

import unittest

from tests import test_lib


class FormattersImportTest(test_lib.ImportCheckTestCase):
  """Tests that CLI helper classes are imported correctly."""

  _IGNORABLE_FILES = frozenset([
      'default.py', 'interface.py', 'logger.py', 'manager.py', 'mediator.py',
      'yaml_formatters_file.py'])

  def testFormattersImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(
        test_lib.CLI_HELPERS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
