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

    application_expected = (
        u'C:\\Program Files (x86)\\Google\\Update\\GoogleUpdate.exe')
    self.assertEqual(event_object.application, application_expected)

    username_expected = u'Brian'
    self.assertEqual(event_object.username, username_expected)

    description_expected = eventdata.EventTimestamp.LAST_RUNTIME
    self.assertEqual(event_object.timestamp_desc, description_expected)

    trigger_expected = u'DAILY'
    self.assertEqual(event_object.trigger, trigger_expected)

    comment_expected = (
        u'Keeps your Google software up to date. If this task is disabled or '
        u'stopped, your Google software will not be kept up to date, meaning '
        u'security vulnerabilities that may arise cannot be fixed and '
        u'features may not work. This task uninstalls itself when there is '
        u'no Google software using it.')
    self.assertEqual(event_object.comment, comment_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-24 12:42:00.112')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Parse second event. Same metadata; different timestamp event.
    event_object = event_objects[1]

    self.assertEqual(event_object.application, application_expected)
    self.assertEqual(event_object.username, username_expected)
    self.assertEqual(event_object.trigger, trigger_expected)
    self.assertEqual(event_object.comment, comment_expected)

    description_expected = u'Scheduled To Start'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 15:42:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'Application: C:\\Program Files (x86)\\Google\\Update\\'
        u'GoogleUpdate.exe /ua /installsource scheduler '
        u'Scheduled by: Brian '
        u'Run Iteration: DAILY')

    expected_msg_short = (
        u'Application: C:\\Program Files (x86)\\Google\\Update\\'
        u'GoogleUpdate.exe /ua /insta...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
