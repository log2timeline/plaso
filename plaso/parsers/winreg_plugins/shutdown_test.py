#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the LastShutdown value plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import shutdown


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class ShutdownPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the LastShutdown value plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = shutdown.ShutdownPlugin()

  def testProcess(self):
    """Tests the Process function."""
    knowledge_base_values = {'current_control_set': u'ControlSet001'}
    test_file_entry = self._GetTestFileEntryFromPath(['SYSTEM'])
    key_path = u'\\ControlSet001\\Control\\Windows'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, knowledge_base_values=knowledge_base_values,
        file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]

    self.assertEquals(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEquals(event_object.parser, self._plugin.plugin_name)

    expected_value = u'ShutdownTime'
    self._TestRegvalue(event_object, u'Description', expected_value)

    expected_msg = (
        u'[\\ControlSet001\\Control\\Windows] '
        u'Description: ShutdownTime')

    # Match UTC timestamp.
    time = long(timelib_test.CopyStringToTimestamp(
        u'2012-04-04 01:58:40.839249'))
    self.assertEquals(event_object.timestamp, time)

    expected_msg_short = (
        u'[\\ControlSet001\\Control\\Windows] '
        u'Description: ShutdownTime')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
