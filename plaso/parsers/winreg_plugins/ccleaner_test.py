#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CCleaner Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import ccleaner
from plaso.parsers.winreg_plugins import test_lib


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the CCleaner Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = ccleaner.CCleanerPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath(['NTUSER-CCLEANER.DAT'])
    key_path = u'\\Software\\Piriform\\CCleaner'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 17)

    event_object = event_objects[0]

    self.assertEquals(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEquals(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-13 10:03:14')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'UpdateKey'
    expected_value = u'07/13/2013 10:03:14 AM'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_string = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[2]

    self.assertEquals(event_object.timestamp, 0)

    regvalue_identifier = u'(App)Delete Index.dat files'
    expected_value = u'True'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_string = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
