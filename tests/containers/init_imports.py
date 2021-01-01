#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all containers are imported correctly."""

import unittest

from tests import test_lib


class ContainersImportTest(test_lib.ImportCheckTestCase):
  """Tests that container classes are imported correctly."""

  _IGNORABLE_FILES = frozenset(['manager.py', 'interface.py'])

  def testContainersImported(self):
    """Tests that all parsers are imported."""
    self._AssertFilesImportedInInit(
        test_lib.CONTAINERS_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
