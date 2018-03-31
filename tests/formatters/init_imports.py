#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests that all formatters are imported correctly."""

from __future__ import unicode_literals

import os
import unittest

from tests import test_lib


class FormattersImportTest(test_lib.ImportCheckTestCase):
  """Tests that CLI helper classes are imported correctly."""

  _CLI_HELPERS_PATH = os.path.join(os.getcwd(), 'plaso', 'formatters')
  _IGNORABLE_FILES = frozenset([
      'default.py', 'interface.py', 'logger.py', 'manager.py', 'mediator.py',
      'winevt_rc.py'])

  def testFormattersImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(
        self._CLI_HELPERS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
