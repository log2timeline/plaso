#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the REGF Windows Registry back-end."""

import unittest

from plaso.dfwinreg import regf

from tests.dfwinreg import test_lib


class REGFWinRegistryFileTest(test_lib.WinRegTestCase):
  """Tests for the REGF Windows Registry file object."""

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    test_file = self._GetTestFilePath([u'NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)
    registry_file.Close()

  def testGetRootKey(self):
    """Tests the GetRootKey function."""
    test_file = self._GetTestFilePath([u'NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)

    registry_key = registry_file.GetRootKey()
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, u'\\')

    registry_file.Close()

    test_file = self._GetTestFilePath([u'ntuser.dat.LOG'])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)

    root_key = registry_file.GetRootKey()
    self.assertIsNone(root_key)

  def testGetKeyByPath(self):
    """Tests the GetKeyByPath function."""
    test_file = self._GetTestFilePath([u'NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)

    key_path = u'\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    key_path = u'\\Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    registry_file.Close()

  def testRecurseKeys(self):
    """Tests the RecurseKeys function."""
    test_file = self._GetTestFilePath([u'NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)
    registry_keys = list(registry_file.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 1127)

    test_file = self._GetTestFilePath([u'ntuser.dat.LOG'])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)
    registry_keys = list(registry_file.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 0 )


class REGFWinRegistryKeyTest(test_lib.WinRegTestCase):
  """Tests for the REGF Windows Registry key object."""

  def testGetSubkeyByName(self):
    """Tests the GetSubkeyByName function."""
    test_file = self._GetTestFilePath([u'NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)

    registry_key = registry_file.GetRootKey()

    key_name = u'Software'
    subkey = registry_key.GetSubkeyByName(key_name)
    self.assertIsNotNone(subkey)
    self.assertEqual(subkey.name, key_name)

    key_name = u'Bogus'
    subkey = registry_key.GetSubkeyByName(key_name)
    self.assertIsNone(subkey)

    registry_file.Close()

  def testGetSubkeys(self):
    """Tests the GetSubkeys function."""
    test_file = self._GetTestFilePath([u'NTUSER.DAT'])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)

    key_path = u'\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)

    subkeys = list(registry_key.GetSubkeys())
    self.assertEqual(len(subkeys), 7)

    registry_file.Close()


if __name__ == '__main__':
  unittest.main()
