#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the USBStor Windows Registry plugin."""

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import usbstor

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class USBStorPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the USBStor Windows Registry plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry([u'SYSTEM'])
    key_path = u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USBSTOR'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = usbstor.USBStorPlugin()
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
        u'2012-04-07 10:31:37.640871')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    expected_value = u'Disk&Ven_HP&Prod_v100w&Rev_1024'
    self._TestRegvalue(event, u'subkey_name', expected_value)

    self._TestRegvalue(event, u'device_type', u'Disk')
    self._TestRegvalue(event, u'vendor', u'Ven_HP')
    self._TestRegvalue(event, u'product', u'Prod_v100w')
    self._TestRegvalue(event, u'revision', u'Rev_1024')

    expected_message = (
        u'[{0:s}] '
        u'device_type: Disk '
        u'friendly_name: HP v100w USB Device '
        u'product: Prod_v100w '
        u'revision: Rev_1024 '
        u'serial: AA951D0000007252&0 '
        u'subkey_name: Disk&Ven_HP&Prod_v100w&Rev_1024 '
        u'vendor: Ven_HP').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
