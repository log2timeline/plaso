#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the USB Windows Registry plugin."""

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import usb

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class USBPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the USB Windows Registry plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry([u'SYSTEM'])
    key_path = u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Enum\\USB'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin_object = usb.USBPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin_object, file_entry=test_file_entry)

    self.assertEqual(len(storage_writer.events), 7)

    event_object = storage_writer.events[3]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    expected_value = u'VID_0E0F&PID_0002'
    self._TestRegvalue(event_object, u'subkey_name', expected_value)
    self._TestRegvalue(event_object, u'vendor', u'VID_0E0F')
    self._TestRegvalue(event_object, u'product', u'PID_0002')

    # Match UTC timestamp.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-07 10:31:37.625246')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'product: PID_0002 '
        u'serial: 6&2ab01149&0&2 '
        u'subkey_name: VID_0E0F&PID_0002 '
        u'vendor: VID_0E0F').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
