#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MountPoints2 Windows Registry plugin."""

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import mountpoints

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class MountPoints2PluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the MountPoints2 Windows Registry plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'NTUSER-WIN7.DAT'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\MountPoints2')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin_object = mountpoints.MountPoints2Plugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin_object, file_entry=test_file_entry)

    self.assertEqual(len(storage_writer.events), 5)

    event_object = storage_writer.events[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-08-23 17:10:14.960960')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue = event_object.regvalue
    self.assertEqual(regvalue.get(u'Share_Name'), u'\\home\\nfury')

    expected_message = (
        u'[{0:s}] Label: Home Drive Remote_Server: controller Share_Name: '
        u'\\home\\nfury Type: Remote Drive Volume: '
        u'##controller#home#nfury').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
