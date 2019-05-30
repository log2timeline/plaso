#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the USBStor Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.winreg_plugins import usbstor

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class USBStorPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the USBStor Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = usbstor.USBStorPlugin()

    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USBSTOR'
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  @shared_test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry(['SYSTEM'])
    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USBSTOR'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = usbstor.USBStorPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.CheckTimestamp(event.timestamp, '2012-04-07 10:31:37.640871')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    expected_value = 'Disk&Ven_HP&Prod_v100w&Rev_1024'
    self._TestRegvalue(event, 'subkey_name', expected_value)

    self._TestRegvalue(event, 'device_type', 'Disk')
    self._TestRegvalue(event, 'vendor', 'Ven_HP')
    self._TestRegvalue(event, 'product', 'Prod_v100w')
    self._TestRegvalue(event, 'revision', 'Rev_1024')

    expected_message = (
        '[{0:s}] '
        'device_type: Disk '
        'friendly_name: HP v100w USB Device '
        'product: Prod_v100w '
        'revision: Rev_1024 '
        'serial: AA951D0000007252&0 '
        'subkey_name: Disk&Ven_HP&Prod_v100w&Rev_1024 '
        'vendor: Ven_HP').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
