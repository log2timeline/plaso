#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the LastShutdown value plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import shutdown

from tests.parsers.winreg_plugins import test_lib


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class ShutdownPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the LastShutdown value plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = shutdown.ShutdownPlugin()

  def testProcess(self):
    """Tests the Process function."""
    knowledge_base_values = {u'current_control_set': u'ControlSet001'}
    test_file_entry = self._GetTestFileEntryFromPath([u'SYSTEM'])
    key_path = u'\\ControlSet001\\Control\\Windows'
    registry_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, knowledge_base_values=knowledge_base_values,
        file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_value = u'ShutdownTime'
    self._TestRegvalue(event_object, u'Description', expected_value)

    # Match UTC timestamp.
    time = long(timelib.Timestamp.CopyFromString(
        u'2012-04-04 01:58:40.839249'))
    self.assertEqual(event_object.timestamp, time)

    expected_message = (
        u'[\\ControlSet001\\Control\\Windows] '
        u'Description: ShutdownTime')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
