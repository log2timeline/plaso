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
    plugin_object = appusage.ApplicationUsagePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'application_usage.sqlite'], plugin_object)

    # The sqlite database contains 5 events.
    self.assertEqual(storage_writer.number_of_events, 5)

    # Check the first event.
    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-05-07 18:52:02')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.application, u'/Applications/Safari.app')
    self.assertEqual(event_object.app_version, u'9537.75.14')
    self.assertEqual(event_object.bundle_id, u'com.apple.Safari')
    self.assertEqual(event_object.count, 1)

    expected_msg = (
        u'/Applications/Safari.app v.9537.75.14 '
        u'(bundle: com.apple.Safari). '
        u'Launched: 1 time(s)')

    expected_msg_short = u'/Applications/Safari.app (1 time(s))'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
