#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MountPoints2 Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import mountpoints

from tests.parsers.winreg_plugins import test_lib


class MountPoints2PluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the MountPoints2 Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = mountpoints.MountPoints2Plugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = self._plugin.REG_KEYS[0]
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 5)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-08-23 17:10:14.960960')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue = event_object.regvalue
    self.assertEqual(regvalue.get(u'Share_Name'), u'\\home\\nfury')

    expected_string = (
        u'[{0:s}] Label: Home Drive Remote_Server: controller Share_Name: '
        u'\\home\\nfury Type: Remote Drive Volume: '
        u'##controller#home#nfury').format(key_path)
    expected_string_short = u'{0:s}...'.format(expected_string[0:77])

    self._TestGetMessageStrings(
        event_object, expected_string, expected_string_short)


if __name__ == '__main__':
  unittest.main()
