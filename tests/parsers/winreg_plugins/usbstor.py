#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the USBStor Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import usbstor

from tests.parsers.winreg_plugins import test_lib


class USBStorPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the USBStor Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = usbstor.USBStorPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'SYSTEM'])
    key_path = u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USBSTOR'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 3)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-07 10:31:37.640871')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_value = u'Disk&Ven_HP&Prod_v100w&Rev_1024'
    self._TestRegvalue(event_object, u'subkey_name', expected_value)

    self._TestRegvalue(event_object, u'device_type', u'Disk')
    self._TestRegvalue(event_object, u'vendor', u'Ven_HP')
    self._TestRegvalue(event_object, u'product', u'Prod_v100w')
    self._TestRegvalue(event_object, u'revision', u'Rev_1024')

    expected_message = (
        u'[{0:s}] '
        u'device_type: Disk '
        u'friendly_name: HP v100w USB Device '
        u'product: Prod_v100w '
        u'revision: Rev_1024 '
        u'serial: AA951D0000007252&0 '
        u'subkey_name: Disk&Ven_HP&Prod_v100w&Rev_1024 '
        u'vendor: Ven_HP').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
