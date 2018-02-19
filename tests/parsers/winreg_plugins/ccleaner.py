#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the CCleaner Windows Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import ccleaner

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class CCleanerRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the CCleaner Windows Registry plugin."""

  def testFilters(self):
    """Tests the FILTERS class attribute."""
    plugin = ccleaner.CCleanerPlugin()

    key_path = 'HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner'
    self._AssertFiltersOnKeyPath(plugin, key_path)

    self._AssertNotFiltersOnKeyPath(plugin, 'HKEY_LOCAL_MACHINE\\Bogus')

  @shared_test_lib.skipUnlessHasTestFile(['NTUSER-CCLEANER.DAT'])
  def testProcess(self):
    """Tests the Process function."""
    plugin = ccleaner.CCleanerPlugin()
    test_file_entry = self._GetTestFileEntry(['NTUSER-CCLEANER.DAT'])
    key_path = 'HKEY_CURRENT_USER\\Software\\Piriform\\CCleaner'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-07-13 10:03:14')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = 'Origin: {0:s}'.format(key_path)
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-07-13 14:03:26.861688')
    self.assertEqual(event.timestamp, expected_timestamp)

    regvalue_identifier = '(App)Delete Index.dat files'
    expected_value = 'True'
    self._TestRegvalue(event, regvalue_identifier, expected_value)

    expected_message = (
        '[{0:s}] '
        '(App)Cookies: True '
        '(App)Delete Index.dat files: True '
        '(App)History: True '
        '(App)Last Download Location: True '
        '(App)Other Explorer MRUs: True '
        '(App)Recent Documents: True '
        '(App)Recently Typed URLs: True '
        '(App)Run (in Start Menu): True '
        '(App)Temporary Internet Files: True '
        '(App)Thumbnail Cache: True '
        'CookiesToSave: *.piriform.com '
        'WINDOW_HEIGHT: 524 '
        'WINDOW_LEFT: 146 '
        'WINDOW_MAX: 0 '
        'WINDOW_TOP: 102 '
        'WINDOW_WIDTH: 733').format(key_path)
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
