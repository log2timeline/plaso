#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari history plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.lib import timelib_test
from plaso.parsers import plist
from plaso.parsers.plist_plugins import safari
from plaso.parsers.plist_plugins import test_lib


class SafariPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Safari history plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = safari.SafariHistoryPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'History.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # 18 entries in timeline.
    self.assertEquals(len(event_objects), 18)

    event_object = event_objects[8]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-08 17:31:00')
    self.assertEquals(event_objects[10].timestamp, expected_timestamp)
    expected_url = u'http://netverslun.sci-mx.is/aminosyrur'
    self.assertEquals(event_object.url, expected_url)

    expected_string = (
        u'Visited: {0:s} (Am\xedn\xf3s\xfdrur ) Visit Count: 1').format(
            expected_url)

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
