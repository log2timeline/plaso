#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X application usage database plugin."""

import unittest

from plaso.formatters import appusage  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import appusage

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class ApplicationUsagePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Mac OS X application usage activity database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'application_usage.sqlite'])
  def testProcess(self):
    """Tests the Process function."""
    plugin = appusage.ApplicationUsagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'application_usage.sqlite'], plugin)

    # The sqlite database contains 5 events.
    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # Check the first event.
    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-05-07 18:52:02')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.application, u'/Applications/Safari.app')
    self.assertEqual(event.app_version, u'9537.75.14')
    self.assertEqual(event.bundle_id, u'com.apple.Safari')
    self.assertEqual(event.count, 1)

    expected_message = (
        u'/Applications/Safari.app v.9537.75.14 '
        u'(bundle: com.apple.Safari). '
        u'Launched: 1 time(s)')

    expected_short_message = u'/Applications/Safari.app (1 time(s))'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
