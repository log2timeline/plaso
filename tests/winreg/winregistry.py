#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the Windows Registry library."""

import unittest

from plaso.winreg import winregistry

from tests.winreg import test_lib


class RegistryUnitTest(test_lib.WinRegTestCase):
  """Tests for the Windows Registry library."""

  def testMountFile(self):
    """Tests mounting REGF files in the Registry."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = self._GetTestFilePath(['SOFTWARE'])
    file_entry = self._GetTestFileEntry(test_file)
    winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    registry.MountFile(winreg_file, u'HKEY_LOCAL_MACHINE\\Software')

    test_file = self._GetTestFilePath(['NTUSER-WIN7.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

    with self.assertRaises(KeyError):
      registry.MountFile(winreg_file, u'HKEY_LOCAL_MACHINE\\Software')

    registry.MountFile(winreg_file, u'HKEY_CURRENT_USER')


if __name__ == '__main__':
  unittest.main()
