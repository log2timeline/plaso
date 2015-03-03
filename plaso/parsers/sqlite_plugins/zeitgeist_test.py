#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Zeitgeist activity database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import zeitgeist as zeitgeist_formatter
from plaso.lib import timelib_test
from plaso.parsers.sqlite_plugins import test_lib
from plaso.parsers.sqlite_plugins import zeitgeist


class ZeitgeistPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Zeitgeist activity database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = zeitgeist.ZeitgeistPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['activity.sqlite'])
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The sqlite database contains 44 events.
    self.assertEqual(len(event_objects), 44)

    # Check the first event.
    event_object = event_objects[0]

    expected_subject_uri = u'application://rhythmbox.desktop'
    self.assertEqual(event_object.subject_uri, expected_subject_uri)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-22 08:53:19.477')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = u'application://rhythmbox.desktop'
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
