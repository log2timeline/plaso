#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Task Scheduler Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import task_scheduler

from tests.parsers.winreg_plugins import test_lib


class TaskCachePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Task Cache key Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = task_scheduler.TaskCachePlugin()

  def testProcess(self):
    """Tests the Process function."""
    key_path = (
        u'\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\TaskCache')
    test_file_entry = self._GetTestFileEntryFromPath([u'SOFTWARE-RunTests'])
    registry_key = self._GetKeyFromFileEntry(test_file_entry, key_path)

    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 174)

    event_object = event_objects[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 04:53:25.811618')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'Task: SynchronizeTime'
    expected_value = u'[ID: {044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}]'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_message = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    event_object = event_objects[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 05:08:50.811626')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'Task: SynchronizeTime'

    expected_message = (
        u'Task: SynchronizeTime '
        u'[Identifier: {044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}]')
    expected_short_message = (
        u'Task: SynchronizeTime')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
