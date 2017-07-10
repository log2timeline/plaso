#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the LastShutdown value plugin."""

import unittest

from plaso.formatters import shutdown  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import shutdown

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class ShutdownPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the LastShutdown value plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry([u'SYSTEM'])
    key_path = u'HKEY_LOCAL_MACHINE\\System\\ControlSet001\\Control\\Windows'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = shutdown.ShutdownPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    self.assertEqual(event.value_name, u'ShutdownTime')

    # Match UTC timestamp.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-04 01:58:40.839249')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_SHUTDOWN)

    expected_message = (
        u'[{0:s}] '
        u'Description: ShutdownTime').format(key_path)
    expected_short_message = u'ShutdownTime'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
