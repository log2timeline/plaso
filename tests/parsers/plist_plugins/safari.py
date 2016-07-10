#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari history plist plugin."""

import unittest

from plaso.formatters import plist as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.plist_plugins import safari

from tests.parsers.plist_plugins import test_lib


class SafariPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Safari history plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'History.plist'

    plugin_object = safari.SafariHistoryPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 18)

    event_object = storage_writer.events[10]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-08 17:31:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = storage_writer.events[8]

    expected_url = u'http://netverslun.sci-mx.is/aminosyrur'
    self.assertEqual(event_object.url, expected_url)

    expected_message = (
        u'Visited: {0:s} (Am\xedn\xf3s\xfdrur ) '
        u'Visit Count: 1').format(expected_url)

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
