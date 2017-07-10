#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Scheduled Task job file parser."""

import unittest

from plaso.formatters import winjob  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import winjob

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinJobTest(test_lib.ParserTestCase):
  """Tests for the Windows Scheduled Task job file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'wintask.job'])
  def testParse(self):
    """Tests the Parse function."""
    parser = winjob.WinJobParser()
    storage_writer = self._ParseFile([u'wintask.job'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-24 12:42:00.112')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_RUN)

    expected_application = (
        u'C:\\Program Files (x86)\\Google\\Update\\GoogleUpdate.exe')
    self.assertEqual(event.application, expected_application)

    self.assertEqual(event.username, u'Brian')

    expected_comment = (
        u'Keeps your Google software up to date. If this task is disabled or '
        u'stopped, your Google software will not be kept up to date, meaning '
        u'security vulnerabilities that may arise cannot be fixed and '
        u'features may not work. This task uninstalls itself when there is '
        u'no Google software using it.')
    self.assertEqual(event.comment, expected_comment)

    # Parse second event. Same metadata; different timestamp event.
    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-12 15:42:00')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.timestamp_desc, u'Scheduled to start')

    self.assertEqual(event.trigger_type, 1)

    expected_message = (
        u'Application: {0:s} /ua /installsource scheduler '
        u'Scheduled by: Brian '
        u'Trigger type: DAILY').format(expected_application)

    expected_short_message = (
        u'Application: {0:s} /ua /insta...').format(expected_application)

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
