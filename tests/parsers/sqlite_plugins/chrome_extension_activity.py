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
    plugin_object = chrome_extension_activity.ChromeExtensionActivityPlugin()
    cache = sqlite.SQLiteCache()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'Extension Activity'], plugin_object, cache=cache)

    self.assertEqual(storage_writer.number_of_events, 56)

    event_object = storage_writer.events[0]

    self.assertEqual(
        event_object.timestamp_desc, definitions.TIME_DESCRIPTION_UNKNOWN)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-25 21:08:23.698737')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_extension_id = u'ognampngfcbddbfemdapefohjiobgbdl'
    self.assertEqual(event_object.extension_id, expected_extension_id)

    self.assertEqual(event_object.action_type, 1)
    self.assertEqual(event_object.activity_id, 48)
    self.assertEqual(event_object.api_name, u'browserAction.onClicked')

    expected_msg = (
        u'Chrome extension: ognampngfcbddbfemdapefohjiobgbdl '
        u'Action type: API event callback (type 1) '
        u'Activity identifier: 48 '
        u'API name: browserAction.onClicked')
    expected_short = (
        u'ognampngfcbddbfemdapefohjiobgbdl browserAction.onClicked')

    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
