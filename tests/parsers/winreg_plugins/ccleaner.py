#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CCleaner Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import ccleaner

from tests.parsers.winreg_plugins import test_lib


__author__ = 'Marc Seguin (segumarc@gmail.com)'


class CCleanerRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the CCleaner Windows Registry plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = ccleaner.CCleanerPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-CCLEANER.DAT'])
    key_path = u'HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-13 10:03:14')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = u'Origin: {0:s}'.format(key_path)
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message)

    event_object = event_objects[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-13 14:03:26.861688')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'(App)Delete Index.dat files'
    expected_value = u'True'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_message = (
        u'[{0:s}] '
        u'(App)Cookies: True '
        u'(App)Delete Index.dat files: True '
        u'(App)History: True '
        u'(App)Last Download Location: True '
        u'(App)Other Explorer MRUs: True '
        u'(App)Recent Documents: True '
        u'(App)Recently Typed URLs: True '
        u'(App)Run (in Start Menu): True '
        u'(App)Temporary Internet Files: True '
        u'(App)Thumbnail Cache: True '
        u'CookiesToSave: *.piriform.com '
        u'WINDOW_HEIGHT: 524 '
        u'WINDOW_LEFT: 146 '
        u'WINDOW_MAX: 0 '
        u'WINDOW_TOP: 102 '
        u'WINDOW_WIDTH: 733').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
