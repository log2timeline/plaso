#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the USBStor Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.winreg_plugins import usbstor

from tests.parsers.winreg_plugins import test_lib


class USBStorPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the USBStor Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = usbstor.USBStorPlugin()

    key_path = 'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USBSTOR'
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

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

    self.CheckTimestamp(event.timestamp, '2012-04-07 10:31:37.640871')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_data.parser, plugin.plugin_name)
    self.assertEqual(event_data.data_type, 'windows:registry:usbstor')
    self.assertEqual(event_data.pathspec, test_file_entry.path_spec)
    self.assertEqual(event_data.subkey_name, 'Disk&Ven_HP&Prod_v100w&Rev_1024')
    self.assertEqual(event_data.device_type, 'Disk')
    self.assertEqual(event_data.vendor, 'Ven_HP')
    self.assertEqual(event_data.product, 'Prod_v100w')
    self.assertEqual(event_data.revision, 'Rev_1024')

    expected_message = (
        '[{0:s}] '
        'Device type: Disk '
        'Display name: HP v100w USB Device '
        'Product: Prod_v100w '
        'Revision: Rev_1024 '
        'Serial: AA951D0000007252&0 '
        'Subkey name: Disk&Ven_HP&Prod_v100w&Rev_1024 '
        'Vendor: Ven_HP').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
