#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the BagMRU Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import bagmru

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class TestBagMRUWindowsRegistryPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the BagMRU plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = bagmru.BagMRUWindowsRegistryPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\ShellNoRoam\\'
        'BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\'
        'Microsoft\\Windows\\Shell\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\'
        'Microsoft\\Windows\\ShellNoRoam\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Local Settings\\Software\\Microsoft\\Windows\\'
        'Shell\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Local Settings\\Software\\Microsoft\\Windows\\'
        'ShellNoRoam\\BagMRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  @shared_test_lib.skipUnlessHasTestFile(['NTUSER.DAT'])
  def testProcess(self):
    """Tests the Process function."""
    plugin = bagmru.BagMRUWindowsRegistryPlugin()
    test_file_entry = self._GetTestFileEntry(['NTUSER.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 15)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.CheckTimestamp(event.timestamp, '2009-08-04 15:19:16.997750')

    expected_message = (
        '[{0:s}] '
        'Index: 1 [MRU Value 0]: '
        'Shell item path: <My Computer>').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2009-08-04 15:19:10.669625')

    expected_message = (
        '[{0:s}\\0] '
        'Index: 1 [MRU Value 0]: '
        'Shell item path: <My Computer> C:\\').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[14]

    self.CheckTimestamp(event.timestamp, '2009-08-04 15:19:16.997750')

    # The winreg_formatter will add a space after the key path even when there
    # is not text.
    expected_message = '[{0:s}\\0\\0\\0\\0\\0] '.format(key_path)

    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
