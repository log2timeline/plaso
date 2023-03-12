#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry plugin interface."""

import unittest

from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.containers import sessions
from plaso.parsers.winreg_plugins import interface
from plaso.storage.fake import writer as fake_writer

from tests.parsers.winreg_plugins import test_lib


class BaseWindowsRegistryKeyFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows Registry key filter interface."""

  def testKeyPaths(self):
    """Tests the key_paths property."""
    path_filter = interface.BaseWindowsRegistryKeyFilter()
    self.assertEqual(path_filter.key_paths, [])


class WindowsRegistryKeyPathFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows Registry key path filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    path_filter = interface.WindowsRegistryKeyPathFilter(
        'HKEY_LOCAL_MACHINE\\System')
    self.assertIsNotNone(path_filter)

  def testKeyPaths(self):
    """Tests the key_paths property."""
    path_filter = interface.WindowsRegistryKeyPathFilter(
        'HKEY_LOCAL_MACHINE\\System')
    self.assertEqual(path_filter.key_paths, ['HKEY_LOCAL_MACHINE\\System'])

    path_filter = interface.WindowsRegistryKeyPathFilter(
        'HKEY_CURRENT_USER\\Software\\Microsoft')
    self.assertEqual(path_filter.key_paths, [
        'HKEY_CURRENT_USER\\Software\\Microsoft',
        'HKEY_CURRENT_USER\\Software\\Wow6432Node\\Microsoft'])

  def testMatch(self):
    """Tests the Match function."""
    path_filter = interface.WindowsRegistryKeyPathFilter(
        'HKEY_LOCAL_MACHINE\\System')

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'System', key_path='HKEY_LOCAL_MACHINE\\System')

    result = path_filter.Match(registry_key)
    self.assertTrue(result)

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Select', key_path='HKEY_LOCAL_MACHINE\\System\\Select')

    result = path_filter.Match(registry_key)
    self.assertFalse(result)

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Software', key_path='HKEY_LOCAL_MACHINE\\Software')

    result = path_filter.Match(registry_key)
    self.assertFalse(result)


class WindowsRegistryKeyPathPrefixFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for Windows Registry key path prefix filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    path_filter = interface.WindowsRegistryKeyPathPrefixFilter(
        'HKEY_LOCAL_MACHINE\\System')
    self.assertIsNotNone(path_filter)

  def testKeyPaths(self):
    """Tests the key_paths property."""
    path_filter = interface.WindowsRegistryKeyPathPrefixFilter(
        'HKEY_LOCAL_MACHINE\\System')
    self.assertEqual(path_filter.key_paths, [])

  def testMatch(self):
    """Tests the Match function."""
    path_filter = interface.WindowsRegistryKeyPathPrefixFilter(
        'HKEY_LOCAL_MACHINE\\System')

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'System', key_path='HKEY_LOCAL_MACHINE\\System')

    result = path_filter.Match(registry_key)
    self.assertTrue(result)

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Select', key_path='HKEY_LOCAL_MACHINE\\System\\Select')

    result = path_filter.Match(registry_key)
    self.assertTrue(result)

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Software', key_path='HKEY_LOCAL_MACHINE\\Software')

    result = path_filter.Match(registry_key)
    self.assertFalse(result)


class WindowsRegistryKeyPathSuffixFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for Windows Registry key path suffix filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    path_filter = interface.WindowsRegistryKeyPathSuffixFilter(
        'Windows\\Explorer')
    self.assertIsNotNone(path_filter)

  def testKeyPaths(self):
    """Tests the key_paths property."""
    path_filter = interface.WindowsRegistryKeyPathSuffixFilter(
        'Windows\\Explorer')
    self.assertEqual(path_filter.key_paths, [])

  def testMatch(self):
    """Tests the Match function."""
    path_filter = interface.WindowsRegistryKeyPathSuffixFilter(
        'Windows\\Explorer')

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Explorer', key_path='HKEY_LOCAL_MACHINE\\Software\\Windows\\Explorer')

    result = path_filter.Match(registry_key)
    self.assertTrue(result)

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Windows', key_path='HKEY_LOCAL_MACHINE\\Software\\Windows')

    result = path_filter.Match(registry_key)
    self.assertFalse(result)

    key_path = 'HKEY_LOCAL_MACHINE\\Software\\Windows\\Explorer\\Zones'
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Explorer', key_path=key_path)

    result = path_filter.Match(registry_key)
    self.assertFalse(result)


class WindowsRegistryKeyWithValuesFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for Windows Registry key with values filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    path_filter = interface.WindowsRegistryKeyWithValuesFilter(
        ('a', 'MRUList'))
    self.assertIsNotNone(path_filter)

  def testKeyPaths(self):
    """Tests the key_paths property."""
    path_filter = interface.WindowsRegistryKeyWithValuesFilter(
        ('a', 'MRUList'))
    self.assertEqual(path_filter.key_paths, [])

  def testMatch(self):
    """Tests the Match function."""
    path_filter = interface.WindowsRegistryKeyWithValuesFilter(
        ('a', 'MRUList'))

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Explorer', key_path='HKEY_LOCAL_MACHINE\\Software\\Windows\\MRU')

    result = path_filter.Match(registry_key)
    self.assertFalse(result)

    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'MRUList', data_type=dfwinreg_definitions.REG_BINARY)
    registry_key.AddValue(registry_value)

    result = path_filter.Match(registry_key)
    self.assertFalse(result)

    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'a', data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    result = path_filter.Match(registry_key)
    self.assertTrue(result)


class WindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows Registry plugin interface."""

  # pylint: disable=protected-access

  def testGetValuesFromKey(self):
    """Tests the _GetValuesFromKey function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    parser_mediator = self._CreateParserMediator(session, storage_writer)

    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'Explorer', key_path='HKEY_LOCAL_MACHINE\\Software\\Windows\\MRU')

    value_data = b'a\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'MRUList', data=value_data, data_type=dfwinreg_definitions.REG_BINARY)
    registry_key.AddValue(registry_value)

    value_data = b'o\x00n\x00e\x00'
    registry_value = dfwinreg_fake.FakeWinRegistryValue(
        'a', data=value_data, data_type=dfwinreg_definitions.REG_SZ)
    registry_key.AddValue(registry_value)

    plugin = interface.WindowsRegistryPlugin()

    expected_value_tuples = [
        ('MRUList', 'REG_BINARY', '(2 bytes)'),
        ('a', 'REG_SZ', 'one')]

    value_tuples = plugin._GetValuesFromKey(parser_mediator, registry_key)
    self.assertEqual(sorted(value_tuples), expected_value_tuples)


if __name__ == '__main__':
  unittest.main()
