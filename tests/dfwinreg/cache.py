#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry objects cache."""

import unittest

from plaso.dfwinreg import cache
from plaso.dfwinreg import registry

from tests.dfwinreg import test_lib


class CacheTest(test_lib.WinRegTestCase):
  """Tests for the Windows Registry objects cache."""

  def testBuildCache(self):
    """Tests creating a Windows Registry objects cache."""
    test_registry = registry.WinRegistry(
        backend=registry.WinRegistry.BACKEND_PYREGF)

    test_file = self._GetTestFilePath([u'SYSTEM'])
    file_entry = self._GetTestFileEntry(test_file)
    winreg_file = test_registry.OpenFileEntry(file_entry, codepage=u'cp1252')

    winreg_cache = cache.WinRegistryCache()

    # Test if this function does not raise an exception.
    winreg_cache.BuildCache(winreg_file, u'SYSTEM')

    self.assertEqual(
        winreg_cache.attributes[u'current_control_set'], u'ControlSet001')


if __name__ == '__main__':
  unittest.main()
