#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the REGF Windows Registry back-end."""

import unittest

from plaso.dfwinreg import regf

from tests.dfwinreg import test_lib


class REGFWinRegTestCase(test_lib.WinRegTestCase):
  """The unit test case for REGF Windows Registry related object."""

  def _OpenREGFRegistryFile(self, filename):
    """Opens a REGF Windows Registry file.

    Args:
      filename: the name of the file relative to the test file path.

    Returns:
      The Windows Registry file object (instance of REGFWinRegistryFileTest) or
      None.
    """
    test_file = self._GetTestFilePath([filename])
    file_entry = self._GetTestFileEntry(test_file)
    file_object = file_entry.GetFileObject()

    registry_file = regf.REGFWinRegistryFile()
    registry_file.Open(file_object)

    return registry_file


class REGFWinRegistryFileTest(REGFWinRegTestCase):
  """Tests for the REGF Windows Registry file object."""

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')
    registry_file.Close()

  def testGetRootKey(self):
    """Tests the GetRootKey function."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    registry_key = registry_file.GetRootKey()
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, u'\\')

    registry_file.Close()

    registry_file = self._OpenREGFRegistryFile(u'ntuser.dat.LOG')

    root_key = registry_file.GetRootKey()
    self.assertIsNone(root_key)

  def testGetKeyByPath(self):
    """Tests the GetKeyByPath function."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    key_path = u'\\'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

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
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    registry_keys = list(registry_file.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 1127)

    registry_file = self._OpenREGFRegistryFile(u'ntuser.dat.LOG')

    registry_keys = list(registry_file.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 0)


class REGFWinRegistryKeyTest(REGFWinRegTestCase):
  """Tests for the REGF Windows Registry key object."""

  def testProperties(self):
    """Tests the properties functions."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    key_path = u'\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.last_written_time, 128938728930133750)
    self.assertEqual(registry_key.name, u'Software')
    self.assertEqual(registry_key.number_of_subkeys, 7)
    self.assertEqual(registry_key.number_of_values, 0)
    self.assertEqual(registry_key.offset, 82652)
    self.assertEqual(registry_key.path, key_path)

    registry_file.Close()

  def testGetSubkeyByName(self):
    """Tests the GetSubkeyByName function."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

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
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    key_path = u'\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)

    subkeys = list(registry_key.GetSubkeys())
    self.assertEqual(len(subkeys), 7)

    registry_file.Close()

  def testGetValueByName(self):
    """Tests the GetValueByName function."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    registry_key = registry_file.GetKeyByPath(u'\\Console')

    value_name = u'ColorTable14'
    registry_value = registry_key.GetValueByName(value_name)
    self.assertIsNotNone(registry_value)
    self.assertEqual(registry_value.name, value_name)

    value_name = u'Bogus'
    registry_value = registry_key.GetValueByName(value_name)
    self.assertIsNone(registry_value)

    # Test retrieving the default (or nameless) value.
    registry_key = registry_file.GetKeyByPath(
        u'\\AppEvents\\EventLabels\\.Default')

    registry_value = registry_key.GetValueByName(u'')
    self.assertIsNotNone(registry_value)
    self.assertIsNone(registry_value.name)

    registry_file.Close()

  def testGetValues(self):
    """Tests the GetValues function."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    key_path = u'\\Console'
    registry_key = registry_file.GetKeyByPath(key_path)

    values = list(registry_key.GetValues())
    self.assertEqual(len(values), 31)

    registry_file.Close()

  def testRecurseKeys(self):
    """Tests the RecurseKeys function."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    key_path = u'\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    registry_keys = list(registry_key.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 797)


class REGFWinRegistryValueTest(REGFWinRegTestCase):
  """Tests for the REGF Windows Registry value object."""

  def testProperties(self):
    """Tests the properties functions."""
    registry_file = self._OpenREGFRegistryFile(u'NTUSER.DAT')

    registry_key = registry_file.GetKeyByPath(u'\\Console')
    value_name = u'ColorTable14'
    registry_value = registry_key.GetValueByName(value_name)
    expected_data = b'\xff\xff\x00\x00'

    self.assertIsNotNone(registry_value)
    self.assertEqual(registry_value.data_type, 4)
    self.assertEqual(registry_value.data_type_string, u'REG_DWORD_LE')
    self.assertEqual(registry_value.GetDataAsObject(), 65535)
    self.assertEqual(registry_value.name, value_name)
    self.assertEqual(registry_value.offset, 29516)
    self.assertEqual(registry_value.data, expected_data)

    registry_key = registry_file.GetKeyByPath(
        u'\\AppEvents\\EventLabels\\CriticalBatteryAlarm')
    value_name = u'DispFileName'
    registry_value = registry_key.GetValueByName(value_name)
    expected_data = (
        b'@\x00m\x00m\x00s\x00y\x00s\x00.\x00c\x00p\x00l\x00,\x00-\x005\x008'
        b'\x002\x007\x00\x00\x00')

    self.assertIsNotNone(registry_value)
    self.assertEqual(registry_value.data_type, 1)
    self.assertEqual(registry_value.data_type_string, u'REG_SZ')
    self.assertEqual(registry_value.GetDataAsObject(), u'@mmsys.cpl,-5827')
    self.assertEqual(registry_value.name, value_name)
    self.assertEqual(registry_value.offset, 6012)
    self.assertEqual(registry_value.data, expected_data)

    registry_key = registry_file.GetKeyByPath(
        u'\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU')
    value_name = u'0'
    registry_value = registry_key.GetValueByName(value_name)
    expected_data = (
        b'\x14\x00\x1fP\xe0O\xd0 \xea:i\x10\xa2\xd8\x08\x00+00\x9d\x00\x00')

    self.assertIsNotNone(registry_value)
    self.assertEqual(registry_value.data_type, 3)
    self.assertEqual(registry_value.data_type_string, u'REG_BINARY')
    self.assertEqual(registry_value.GetDataAsObject(), expected_data)
    self.assertEqual(registry_value.name, value_name)
    self.assertEqual(registry_value.offset, 625588)
    self.assertEqual(registry_value.data, expected_data)

    registry_file.Close()

    registry_file = self._OpenREGFRegistryFile(u'NTUSER-WIN7.DAT')

    registry_key = registry_file.GetKeyByPath(
        u'\\Software\\Microsoft\\Cryptography\\CertificateTemplateCache\\User')
    value_name = u'SupportedCSPs'
    registry_value = registry_key.GetValueByName(value_name)
    expected_string = [
        u'Microsoft Enhanced Cryptographic Provider v1.0',
        u'Microsoft Base Cryptographic Provider v1.0']
    expected_data = (
        b'M\x00i\x00c\x00r\x00o\x00s\x00o\x00f\x00t\x00 \x00E\x00n\x00h\x00a'
        b'\x00n\x00c\x00e\x00d\x00 \x00C\x00r\x00y\x00p\x00t\x00o\x00g\x00r'
        b'\x00a\x00p\x00h\x00i\x00c\x00 \x00P\x00r\x00o\x00v\x00i\x00d\x00e'
        b'\x00r\x00 \x00v\x001\x00.\x000\x00\x00\x00M\x00i\x00c\x00r\x00o'
        b'\x00s\x00o\x00f\x00t\x00 \x00B\x00a\x00s\x00e\x00 \x00C\x00r\x00y'
        b'\x00p\x00t\x00o\x00g\x00r\x00a\x00p\x00h\x00i\x00c\x00 \x00P\x00r'
        b'\x00o\x00v\x00i\x00d\x00e\x00r\x00 \x00v\x001\x00.\x000\x00\x00'
        b'\x00\x00\x00')

    self.assertIsNotNone(registry_value)
    self.assertEqual(registry_value.data_type, 7)
    self.assertEqual(registry_value.data_type_string, u'REG_MULTI_SZ')
    self.assertEqual(registry_value.GetDataAsObject(), expected_string)
    self.assertEqual(registry_value.name, value_name)
    self.assertEqual(registry_value.offset, 241452)
    self.assertEqual(registry_value.data, expected_data)

    registry_file.Close()


if __name__ == '__main__':
  unittest.main()
