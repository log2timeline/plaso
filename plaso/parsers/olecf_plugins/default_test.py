#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) default plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import olecf as olecf_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.olecf_plugins import default
from plaso.parsers.olecf_plugins import test_lib


class TestDefaultPluginOleCf(test_lib.OleCfPluginTestCase):
  """Tests for the OLECF default plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = default.DefaultOleCFPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['Document.doc'])
    event_queue_consumer = self._ParseOleCfFileWithPlugin(
        test_file, self._plugin)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 5)

    # Check the Root Entry event.
    event_object = event_objects[0]

    self.assertEqual(event_object.name, u'Root Entry')

    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-05-16 02:29:49.795')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_string = (
        u'Name: Root Entry')

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # Check one other entry.
    event_object = event_objects[1]

    expected_string = u'Name: MsoDataStore'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-05-16 02:29:49.704')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
