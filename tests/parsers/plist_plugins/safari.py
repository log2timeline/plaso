#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari history plist plugin."""

import unittest

from plaso.formatters import plist as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import safari

from tests.parsers.plist_plugins import test_lib


class SafariPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Safari history plist plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = safari.SafariHistoryPlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'History.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 18)

    event_object = event_objects[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-08 17:31:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = event_objects[9]

    expected_url = u'http://netverslun.sci-mx.is/aminosyrur'
    self.assertEqual(event_object.url, expected_url)

    expected_string = (
        u'Visited: {0:s} (Am\xedn\xf3s\xfdrur ) '
        u'Visit Count: 1').format(expected_url)

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
