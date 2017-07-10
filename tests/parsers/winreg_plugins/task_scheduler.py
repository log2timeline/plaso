#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Task Scheduler Windows Registry plugin."""

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import task_scheduler

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class TaskCachePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Task Cache key Windows Registry plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE-RunTests'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry([u'SOFTWARE-RunTests'])
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
        u'CurrentVersion\\Schedule\\TaskCache')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = task_scheduler.TaskCachePlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 174)

    events = list(storage_writer.GetEvents())

    event = events[0]

    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 04:53:25.811618')
    self.assertEqual(event.timestamp, expected_timestamp)

    regvalue_identifier = u'Task: SynchronizeTime'
    expected_value = u'[ID: {044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}]'
    self._TestRegvalue(event, regvalue_identifier, expected_value)

    expected_message = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-07-14 05:08:50.811626')
    self.assertEqual(event.timestamp, expected_timestamp)

    regvalue_identifier = u'Task: SynchronizeTime'

    expected_message = (
        u'Task: SynchronizeTime '
        u'[Identifier: {044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}]')
    expected_short_message = (
        u'Task: SynchronizeTime')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
