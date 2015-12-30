#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the BagMRU Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import bagmru

from tests.parsers.winreg_plugins import test_lib


class TestBagMRUPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the BagMRU plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = bagmru.BagMRUPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 15)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:19:16.997750')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] '
        u'Index: 1 [MRU Value 0]: '
        u'Shell item path: <My Computer>').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    event_object = event_objects[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:19:10.669625')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}\\0] '
        u'Index: 1 [MRU Value 0]: '
        u'Shell item path: <My Computer> C:\\').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    event_object = event_objects[14]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:19:16.997750')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # The winreg_formatter will add a space after the key path even when there
    # is not text.
    expected_message = u'[{0:s}\\0\\0\\0\\0\\0] '.format(key_path)

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
