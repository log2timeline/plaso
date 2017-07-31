#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome extension activity database plugin."""

import unittest

from plaso.formatters import chrome_extension_activity  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import chrome_extension_activity

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class ChromeExtensionActivityPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome extension activity database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'Extension Activity'])
  def testProcess(self):
    """Tests the Process function on a Chrome extension activity database."""
    plugin = chrome_extension_activity.ChromeExtensionActivityPlugin()
    cache = sqlite.SQLiteCache()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'Extension Activity'], plugin, cache=cache)

    self.assertEqual(storage_writer.number_of_events, 56)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_UNKNOWN)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-25 21:08:23.698737')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_extension_id = u'ognampngfcbddbfemdapefohjiobgbdl'
    self.assertEqual(event.extension_id, expected_extension_id)

    self.assertEqual(event.action_type, 1)
    self.assertEqual(event.activity_id, 48)
    self.assertEqual(event.api_name, u'browserAction.onClicked')

    expected_message = (
        u'Chrome extension: ognampngfcbddbfemdapefohjiobgbdl '
        u'Action type: API event callback (type 1) '
        u'Activity identifier: 48 '
        u'API name: browserAction.onClicked')
    expected_short_message = (
        u'ognampngfcbddbfemdapefohjiobgbdl browserAction.onClicked')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
