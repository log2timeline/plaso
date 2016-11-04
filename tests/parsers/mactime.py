#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the for mactime parser."""

import unittest

from plaso.formatters import mactime  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import mactime

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MactimeTest(test_lib.ParserTestCase):
  """Tests the for mactime parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'mactime.body'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = mactime.MactimeParser()
    storage_writer = self._ParseFile([u'mactime.body'], parser_object)

    # The file contains 13 lines x 4 timestamps per line, which should be
    # 52 events in total. However several of these events have an empty
    # timestamp value and are omitted.
    # Total entries: 11 * 3 + 2 * 4 = 41
    self.assertEqual(len(storage_writer.events), 41)

    # The order in which TextCSVParser generates events is nondeterministic
    # hence we sort the events.
    events = self._GetSortedEvents(storage_writer.events)

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0

    event = events[21]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:43')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEqual(event.inode, 16)

    event = events[22]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:44')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    event = events[23]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:45')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.timestamp_desc, eventdata.EventTimestamp.CHANGE_TIME)

    expected_filename = u'/a_directory/another_file'
    self.assertEqual(event.filename, expected_filename)
    self.assertEqual(event.mode_as_string, u'r/rrw-------')

    self._TestGetMessageStrings(event, expected_filename, expected_filename)


if __name__ == '__main__':
  unittest.main()
