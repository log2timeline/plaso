#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Scheduled Task job file parser."""

import unittest

from plaso.formatters import winjob as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winjob

from tests.parsers import test_lib


class WinJobTest(test_lib.ParserTestCase):
  """Tests for the Windows Scheduled Task job file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = winjob.WinJobParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'wintask.job'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)

    event_object = event_objects[0]

    expected_application = (
        u'C:\\Program Files (x86)\\Google\\Update\\GoogleUpdate.exe')
    self.assertEqual(event_object.application, expected_application)

    self.assertEqual(event_object.username, u'Brian')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_RUNTIME)
    self.assertEqual(event_object.trigger, 1)

    expected_comment = (
        u'Keeps your Google software up to date. If this task is disabled or '
        u'stopped, your Google software will not be kept up to date, meaning '
        u'security vulnerabilities that may arise cannot be fixed and '
        u'features may not work. This task uninstalls itself when there is '
        u'no Google software using it.')
    self.assertEqual(event_object.comment, expected_comment)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-24 12:42:00.112')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Parse second event. Same metadata; different timestamp event.
    event_object = event_objects[1]

    self.assertEqual(event_object.timestamp_desc, u'Scheduled To Start')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 15:42:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'Application: {0:s} /ua /installsource scheduler '
        u'Scheduled by: Brian '
        u'Run Iteration: DAILY').format(expected_application)

    expected_short_message = (
        u'Application: {0:s} /ua /insta...').format(expected_application)

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
