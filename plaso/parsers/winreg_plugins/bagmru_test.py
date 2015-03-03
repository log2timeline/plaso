#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the BagMRU Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import bagmru
from plaso.parsers.winreg_plugins import test_lib


class TestBagMRUPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the BagMRU plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = bagmru.BagMRUPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath(['NTUSER.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU')
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 15)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2009-08-04 15:19:16.997750')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value 0]: '
        u'Shell item list: [My Computer]').format(key_path)

    expected_msg_short = (
        u'[{0:s}] Index: 1 [MRU Value 0]: Shel...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2009-08-04 15:19:10.669625')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'[{0:s}\\0] '
        u'Index: 1 [MRU Value 0]: '
        u'Shell item list: [My Computer, C:\\]').format(key_path)

    expected_msg_short = (
        u'[{0:s}\\0] Index: 1 [MRU Value 0]: Sh...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[14]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2009-08-04 15:19:16.997750')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The winreg_formatter will add a space after the key path even when there
    # is not text.
    expected_msg = u'[{0:s}\\0\\0\\0\\0\\0] '.format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
