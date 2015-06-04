#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the pyregf Windows Registry back-end."""

import unittest

from plaso.winreg import winpyregf

from tests.winreg import test_lib


class RegistryUnitTest(test_lib.WinRegTestCase):
  """Tests for the pyregf Windows Registry back-end."""

  def _KeyPathCompare(self, winreg_file, key_path):
    """Retrieves a key from the file and checks if the path key matches.

    Args:
      winreg_file: the Windows Registry file (instance of WinPyregfFile).
      key_path: the key path to retrieve and compare.
    """
    key = winreg_file.GetKeyByPath(key_path)
    self.assertEqual(key.path, key_path)

  def testListKeys(self):
    test_file = self._GetTestFilePath(['NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    winreg_file = winpyregf.WinRegistry(file_entry)
    keys = list(winreg_file)

    # Count the number of Registry keys in the hive.
    self.assertEqual(len(keys), 1126)

  def testWinPyregf(self):
    test_file = self._GetTestFilePath(['NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    winreg_file = winpyregf.WinPyregfFile()
    winreg_file.Open(file_entry)

    self._KeyPathCompare(winreg_file, u'\\')
    self._KeyPathCompare(winreg_file, u'\\Printers')
    self._KeyPathCompare(winreg_file, u'\\Printers\\Connections')
    self._KeyPathCompare(winreg_file, u'\\Software')


if __name__ == '__main__':
  unittest.main()
