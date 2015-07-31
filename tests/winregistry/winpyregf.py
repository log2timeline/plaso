#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the pyregf Windows Registry back-end."""

import unittest

from plaso.winregistry import regf

from tests.winregistry import test_lib


class WinPyregfFileTest(test_lib.WinRegTestCase):
  """Tests for the pyregf Windows Registry File object."""

  def _KeyPathCompare(self, winreg_file, key_path):
    """Retrieves a key from the file and checks if the path key matches.

    Args:
      winreg_file: the Windows Registry file (instance of WinPyregfFile).
      key_path: the key path to retrieve and compare.
    """
    key = winreg_file.GetKeyByPath(key_path)
    self.assertEqual(key.path, key_path)

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    test_file = self._GetTestFilePath([u'NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    winreg_file = regf.WinPyregfFile()
    winreg_file.OpenFileEntry(file_entry)

    self._KeyPathCompare(winreg_file, u'\\')
    self._KeyPathCompare(winreg_file, u'\\Printers')
    self._KeyPathCompare(winreg_file, u'\\Printers\\Connections')
    self._KeyPathCompare(winreg_file, u'\\Software')

    winreg_file.Close()


if __name__ == '__main__':
  unittest.main()
