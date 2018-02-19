#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MountPoints2 Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import mountpoints

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class MountPoints2PluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the MountPoints2 Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = mountpoints.MountPoints2Plugin()

    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\MountPoints2')
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  @shared_test_lib.skipUnlessHasTestFile(['NTUSER-WIN7.DAT'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['NTUSER-WIN7.DAT'])
    key_path = (
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Explorer\\MountPoints2')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = mountpoints.MountPoints2Plugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2011-08-23 17:10:14.960960')
    self.assertEqual(event.timestamp, expected_timestamp)

    regvalue = event.regvalue
    self.assertEqual(regvalue.get('Share_Name'), '\\home\\nfury')

    expected_message = (
        '[{0:s}] Label: Home Drive Remote_Server: controller Share_Name: '
        '\\home\\nfury Type: Remote Drive Volume: '
        '##controller#home#nfury').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
