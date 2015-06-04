#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MSIE typed URLs Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import typedurls

from tests.parsers.winreg_plugins import test_lib


__author__ = 'David Nides (david.nides@gmail.com)'


class MsieTypedURLsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the MSIE typed URLs Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = typedurls.TypedURLsPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = u'\\Software\\Microsoft\\Internet Explorer\\TypedURLs'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 13)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-12 21:23:53.307749')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'url1'
    expected_value = u'http://cnn.com/'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_string = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    self._TestGetMessageStrings(event_object, expected_string, expected_string)


class TypedPathsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the typed paths Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = typedurls.TypedURLsPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TypedPaths')
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:58:15.811625')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'url1'
    expected_value = u'\\\\controller'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    expected_msg_short = u'[{0:s}] {1:s}: \\\\cont...'.format(
        key_path, regvalue_identifier)
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
