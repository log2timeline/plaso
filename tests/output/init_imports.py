#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests that all output modules are imported correctly."""

from __future__ import unicode_literals

import unittest

from tests import test_lib


class OutputImportTest(test_lib.ImportCheckTestCase):
  """Tests that analysis plugin classes are imported correctly."""

  _IGNORABLE_FILES = frozenset([
      'logger.py', 'manager.py', 'mediator.py', 'interface.py',
      'shared_elastic.py', 'shared_json.py'])

  def testOutputModulesImported(self):
    """Tests that all output modules are imported."""
    self._AssertFilesImportedInInit(test_lib.OUTPUT_PATH, self._IGNORABLE_FILES)


if __name__ == '__main__':
  unittest.main()
