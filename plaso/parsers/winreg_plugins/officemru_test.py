#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Office MRUs Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import officemru
from plaso.parsers.winreg_plugins import test_lib


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRUPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Microsoft Office MRUs Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = officemru.OfficeMRUPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = u'\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU'
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
        u'2012-03-13 18:27:15.083')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'Item 1'
    expected_value = (
        u'[F00000000][T01CD0146EA1EADB0][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\'
        u'SA-23E Mitchell-Hyundyne Starfury.docx')
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    expected_msg_short = u'[{0:s}] {1:s}: [F00000000][T01CD0146...'.format(
        key_path, regvalue_identifier)
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
