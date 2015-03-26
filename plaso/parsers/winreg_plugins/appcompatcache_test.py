#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Application Compatibility Cache key Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import appcompatcache
from plaso.parsers.winreg_plugins import test_lib


class AppCompatCacheRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the AppCompatCache Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = appcompatcache.AppCompatCachePlugin()

  def testProcess(self):
    """Tests the Process function."""
    knowledge_base_values = {'current_control_set': u'ControlSet001'}
    test_file_entry = self._GetTestFileEntryFromPath([u'SYSTEM'])
    key_path = u'\\ControlSet001\\Control\\Session Manager\\AppCompatCache'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)

    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key,
        knowledge_base_values=knowledge_base_values,
        file_entry=test_file_entry, parser_chain=self._plugin.plugin_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 330)

    event_object = event_objects[9]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2012-04-04 01:46:37.932964')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    self.assertEqual(event_object.keyname, key_path)
    expected_msg = (
        u'[{0:s}] Cached entry: 10 Path: '
        u'\\??\\C:\\Windows\\PSEXESVC.EXE'.format(event_object.keyname))

    expected_msg_short = (
        u'Path: \\??\\C:\\Windows\\PSEXESVC.EXE')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
