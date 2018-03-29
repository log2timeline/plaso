#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests that all filters are imported correctly."""

from __future__ import unicode_literals

import os
import unittest

from tests import test_lib


class FiltersImportTest(test_lib.ImportCheckTestCase):
  """Tests that filter classes are imported correctly."""

  _FILTERS_PATH = os.path.join(os.getcwd(), 'plaso', 'filters')
  _IGNORABLE_FILES = frozenset(['interface.py', 'manager.py', 'mediator.py'])

  def testFiltersImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(self._FILTERS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
