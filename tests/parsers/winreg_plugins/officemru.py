#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Office MRUs Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import officemru as _  # pylint: disable=unused-import
from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.winreg_plugins import officemru

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class OfficeMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Microsoft Office MRUs Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = officemru.OfficeMRUPlugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Access\\File MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Access\\Place MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Excel\\File MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Excel\\Place MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'PowerPoint\\File MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'PowerPoint\\Place MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Word\\File MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
        'Word\\Place MRU')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  @shared_test_lib.skipUnlessHasTestFile(['NTUSER-WIN7.DAT'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\Word\\'
        'File MRU')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = officemru.OfficeMRUPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    event = events[5]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.CheckTimestamp(event.timestamp, '2012-03-13 18:27:15.089802')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    regvalue_identifier = 'Item 1'
    expected_value_string = (
        '[F00000000][T01CD0146EA1EADB0][O00000000]*'
        'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\'
        'SA-23E Mitchell-Hyundyne Starfury.docx')
    self._TestRegvalue(event, regvalue_identifier, expected_value_string)

    expected_message = (
        '[{0:s}] '
        '{1:s}: {2:s} '
        'Item 2: [F00000000][T01CD00921FC127F0][O00000000]*'
        'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\Earthforce SA-26 '
        'Thunderbolt Star Fury.docx '
        'Item 3: [F00000000][T01CD009208780140][O00000000]*'
        'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\StarFury.docx '
        'Item 4: [F00000000][T01CCFE0B22DA9EF0][O00000000]*'
        'C:\\Users\\nfury\\Documents\\VIBRANIUM.docx '
        'Item 5: [F00000000][T01CCFCBA595DFC30][O00000000]*'
        'C:\\Users\\nfury\\Documents\\ADAMANTIUM-Background.docx').format(
            key_path, regvalue_identifier, expected_value_string)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test OfficeMRUWindowsRegistryEvent.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2012-03-13 18:27:15.083000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    self.assertEqual(event.value_string, expected_value_string)

    expected_message = '[{0:s}] Value: {1:s}'.format(
        key_path, expected_value_string)
    expected_short_message = '{0:s}...'.format(expected_value_string[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
