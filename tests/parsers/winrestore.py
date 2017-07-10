#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Restore Point (rp.log) file parser."""

import unittest

from plaso.formatters import winrestore  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import winrestore

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class RestorePointLogParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Restore Point (rp.log) file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'rp.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = winrestore.RestorePointLogParser()
    storage_writer = self._ParseFile([u'rp.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-03-23 18:38:14.246954')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.restore_point_event_type, 102)
    self.assertEqual(event.restore_point_type, 0)
    expected_description = u'Software Distribution Service 3.0'
    self.assertEqual(event.description, expected_description)

    expected_message = (
        u'{0:s} '
        u'Event type: BEGIN_NESTED_SYSTEM_CHANGE '
        u'Restore point type: UNKNOWN').format(expected_description)
    expected_short_message = expected_description

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
