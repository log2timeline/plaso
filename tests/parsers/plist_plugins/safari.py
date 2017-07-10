#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari history plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.plist_plugins import safari

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class SafariPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Safari history plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'History.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'History.plist'

    plugin = safari.SafariHistoryPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_events, 18)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-08 17:31:00')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[9]

    expected_url = u'http://netverslun.sci-mx.is/aminosyrur'
    self.assertEqual(event.url, expected_url)

    expected_message = (
        u'Visited: {0:s} (Am\xedn\xf3s\xfdrur ) '
        u'Visit Count: 1').format(expected_url)

    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
