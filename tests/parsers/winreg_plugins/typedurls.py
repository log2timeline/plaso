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
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\'
        u'TypedURLs')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

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

    expected_message = (
        u'[{0:s}] '
        u'url1: http://cnn.com/ '
        u'url10: http://www.adobe.com/ '
        u'url11: http://www.google.com/ '
        u'url12: http://www.firefox.com/ '
        u'url13: http://go.microsoft.com/fwlink/?LinkId=69157 '
        u'url2: http://twitter.com/ '
        u'url3: http://linkedin.com/ '
        u'url4: http://tweetdeck.com/ '
        u'url5: mozilla '
        u'url6: http://google.com/ '
        u'url7: http://controller.shieldbase.local/certsrv/ '
        u'url8: http://controller.shieldbase.local/ '
        u'url9: http://www.stark-research-labs.com/').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


class TypedPathsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the typed paths Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = typedurls.TypedURLsPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\TypedPaths')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
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

    expected_message = u'[{0:s}] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])
    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
