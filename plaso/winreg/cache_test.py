#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry objects cache."""

import unittest

from plaso.winreg import cache
from plaso.winreg import test_lib
from plaso.winreg import winregistry


class CacheTest(test_lib.WinRegTestCase):
  """Tests for the Windows Registry objects cache."""

  def testBuildCache(self):
    """Tests creating a Windows Registry objects cache."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = self._GetTestFilePath(['SYSTEM'])
    file_entry = self._GetTestFileEntry(test_file)
    winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    winreg_cache = cache.WinRegistryCache()

    # Test if this function does not raise an exception.
    winreg_cache.BuildCache(winreg_file, 'SYSTEM')

    self.assertEqual(
        winreg_cache.attributes['current_control_set'], 'ControlSet001')


if __name__ == '__main__':
  unittest.main()
